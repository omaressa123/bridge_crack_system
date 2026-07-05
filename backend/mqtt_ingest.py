"""
MQTT ingest module for the bridge crack backend.

Drop this file into your `backend/` folder next to main.py, then add the
three lines shown at the bottom of this file into main.py to wire it up.

What it does:
1. Subscribes to sensors/+/data on the MQTT broker (the "+" matches any
   bridge_id, so any number of fake or real sensors can publish here).
2. On every message: saves a row into the SensorData table (same table
   your /sensors/data and /bridge/{id}/status endpoints already read from).
3. Immediately pushes the reading to every connected WebSocket client, so
   the React dashboard updates in real time -- no more 60s random mock.

Because this runs against the same DB table and the same WebSocket
connections your backend already uses, nothing on the frontend changes.
When you replace the fake publisher with a real ESP32/Pi + sensor, this
file needs zero changes -- it only ever sees MQTT messages, never cares
who sent them.
"""

import json
import threading

import paho.mqtt.client as mqtt

MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "sensors/+/data"   # + wildcard matches any bridge_id


def start_mqtt_listener(db_session_factory, SensorData, active_websockets, broadcast_fn):
    """
    Call this once, from main.py's startup event.

    Args:
        db_session_factory: your SessionLocal (or equivalent) callable that
            returns a new DB session, e.g. `SessionLocal()`.
        SensorData: your SQLAlchemy SensorData model class.
        active_websockets: a list (or set) of currently connected
            WebSocket objects that main.py already tracks -- or an empty
            list if you don't track this yet (see main.py notes below).
        broadcast_fn: an async function `await broadcast_fn(payload_dict)`
            that sends a dict to every connected websocket. If you don't
            have one yet, a minimal version is given in the main.py
            snippet at the bottom of this file.
    """

    def on_connect(client, userdata, flags, rc):
        print(f"[mqtt_ingest] connected to broker, rc={rc}")
        client.subscribe(MQTT_TOPIC, qos=1)
        print(f"[mqtt_ingest] subscribed to {MQTT_TOPIC}")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except json.JSONDecodeError:
            print(f"[mqtt_ingest] bad payload on {msg.topic}: {msg.payload}")
            return

        # topic looks like: sensors/bridge_1/data
        bridge_id_str = msg.topic.split("/")[1]
        try:
            bridge_id = int(bridge_id_str.replace("bridge_", ""))
        except ValueError:
            bridge_id = bridge_id_str  # fall back to raw string id

        db = db_session_factory()
        try:
            reading = SensorData(
                bridge_id=bridge_id,
                temperature_c=payload.get("temperature"),
                moisture_percent=payload.get("moisture"),
                acceleration_x=payload.get("vibration"),
                strain_gauge_value=payload.get("strain"),
            )
            db.add(reading)
            db.commit()
            print(f"[mqtt_ingest] saved reading for bridge_id={bridge_id}")
        except Exception as e:
            db.rollback()
            print(f"[mqtt_ingest] DB error: {e}")
        finally:
            db.close()

        # Push to connected dashboards in real time.
        if broadcast_fn is not None:
            import asyncio
            payload["bridge_id"] = bridge_id
            try:
                asyncio.run(broadcast_fn(payload))
            except RuntimeError:
                # already inside an event loop (typical in FastAPI) --
                # schedule it instead of blocking
                loop = asyncio.get_event_loop()
                loop.create_task(broadcast_fn(payload))

    client = mqtt.Client(client_id="backend_ingest")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)

    # Run the MQTT network loop in a background thread so it never
    # blocks FastAPI's own event loop.
    thread = threading.Thread(target=client.loop_forever, daemon=True)
    thread.start()
    print("[mqtt_ingest] listener thread started")
    return client


# ---------------------------------------------------------------------------
# Add this to backend/main.py:
# ---------------------------------------------------------------------------
#
#   from mqtt_ingest import start_mqtt_listener
#
#   connected_websockets = []   # if you don't already track these
#
#   async def broadcast_to_dashboards(payload: dict):
#       for ws in list(connected_websockets):
#           try:
#               await ws.send_json(payload)
#           except Exception:
#               connected_websockets.remove(ws)
#
#   @app.on_event("startup")
#   async def on_startup():
#       start_mqtt_listener(SessionLocal, SensorData, connected_websockets, broadcast_to_dashboards)
#
# And in your existing @app.websocket("/ws") handler, replace the random
# mock-data loop with simply appending the socket to connected_websockets
# and awaiting disconnect, e.g.:
#
#   @app.websocket("/ws")
#   async def websocket_endpoint(websocket: WebSocket):
#       await websocket.accept()
#       connected_websockets.append(websocket)
#       try:
#           while True:
#               await websocket.receive_text()   # just keep the connection open
#       except WebSocketDisconnect:
#           connected_websockets.remove(websocket)
# ---------------------------------------------------------------------------
