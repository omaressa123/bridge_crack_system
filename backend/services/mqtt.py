import json
import logging
import os

import paho.mqtt.client as mqtt

from datetime import datetime

from database import SessionLocal
from models import SensorData, SensorDevice

logger = logging.getLogger(__name__)

MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "sensors/+/data")


def start_mqtt_listener(active_websockets, broadcast_fn):
    def on_connect(client, userdata, flags, rc, properties=None):
        logger.info("MQTT connected to broker, rc=%s", rc)
        client.subscribe(MQTT_TOPIC, qos=1)

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except json.JSONDecodeError:
            logger.warning("Bad MQTT payload on %s: %s", msg.topic, msg.payload)
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

            device_id = payload.get("device_id") or f"bridge_{bridge_id}_sensor"
            device = db.query(SensorDevice).filter(SensorDevice.device_id == device_id).first()
            if not device:
                device = SensorDevice(
                    bridge_id=bridge_id,
                    device_id=device_id,
                    mqtt_topic=msg.topic,
                    status="connected",
                )
                db.add(device)
            else:
                device.status = "connected"
                device.last_seen = datetime.utcnow()
                device.mqtt_topic = msg.topic
                device.battery_level = payload.get("battery")
                device.signal_strength = payload.get("signal")

            db.commit()
        except Exception:
            db.rollback()
            logger.exception("MQTT DB error")
        finally:
            db.close()

        if broadcast_fn is not None:
            import asyncio

            payload["bridge_id"] = bridge_id
            try:
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
        logger.info("MQTT listener started on %s:%s", MQTT_BROKER_HOST, MQTT_BROKER_PORT)
    except Exception:
        logger.exception("Failed to connect to MQTT broker")

    return client
