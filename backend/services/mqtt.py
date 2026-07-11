import json
import paho.mqtt.client as mqtt
from database import SessionLocal
from models import SensorData

MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "sensors/+/data"

def start_mqtt_listener(active_websockets, broadcast_fn):
    def on_connect(client, userdata, flags, rc, properties=None):
        print(f"[mqtt_ingest] connected to broker, rc={rc}")
        client.subscribe(MQTT_TOPIC, qos=1)

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except json.JSONDecodeError:
            print(f"[mqtt_ingest] bad payload on {msg.topic}: {msg.payload}")
            return

        bridge_id_str = msg.topic.split("/")[1]
        try:
            bridge_id = int(bridge_id_str.replace("bridge_", ""))
        except ValueError:
            bridge_id = bridge_id_str

        db = SessionLocal()
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
        except Exception as e:
            db.rollback()
            print(f"[mqtt_ingest] DB error: {e}")
        finally:
            db.close()

        if broadcast_fn is not None:
            import asyncio
            payload["bridge_id"] = bridge_id
            try:
                # Try to get existing loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(broadcast_fn(payload))
                else:
                    asyncio.run(broadcast_fn(payload))
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(broadcast_fn(payload))

    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="backend_ingest")
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        client.loop_start()
        print(f"✅ MQTT Listener started on {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
    except Exception as e:
        print(f"❌ Failed to connect to MQTT broker: {e}")
    
    return client
