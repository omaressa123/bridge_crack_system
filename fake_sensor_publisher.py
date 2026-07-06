"""
Fake sensor publisher.

Simulates one or more bridge sensor units publishing readings over MQTT,
exactly as a real ESP32/Raspberry Pi + sensor kit would once you buy the
hardware.

Uses sensor_config.py to toggle between fake and real sensors without
changing any logic here.
"""

import json
import time
from typing import Dict

import paho.mqtt.client as mqtt

from sensor_config import USE_FAKE_SENSORS

# Import sensors based on config
if USE_FAKE_SENSORS:
    from fake_sensors import (
        temp_sensor,
        moisture_sensor,
        accel_sensor,
        strain_sensor
    )
else:
    from real_sensors import (
        temp_sensor,
        moisture_sensor,
        accel_sensor,
        strain_sensor
    )


BROKER_HOST = "localhost"
BROKER_PORT = 1883

# Simulate readings for these bridge IDs. Add more to simulate more bridges.
BRIDGE_IDS = ["bridge_1", "bridge_2"]

PUBLISH_INTERVAL_SECONDS = 5


def generate_reading() -> Dict[str, float]:
    """Build one sensor reading using active (fake or real) sensors."""
    return {
        "temperature": temp_sensor.read(),
        "moisture": moisture_sensor.read(),
        "vibration": accel_sensor.read(),
        "strain": strain_sensor.read(),
    }


def main():
    client = mqtt.Client(client_id="fake_sensor_publisher")
    client.connect(BROKER_HOST, BROKER_PORT)
    client.loop_start()

    sensor_type = "FAKE" if USE_FAKE_SENSORS else "REAL"
    print(f"Publishing {sensor_type} readings for {BRIDGE_IDS} every {PUBLISH_INTERVAL_SECONDS}s "
          f"to broker {BROKER_HOST}:{BROKER_PORT}. Ctrl+C to stop.")

    try:
        while True:
            for bridge_id in BRIDGE_IDS:
                reading = generate_reading()
                reading["bridge_id"] = bridge_id
                reading["timestamp"] = time.time()

                topic = f"sensors/{bridge_id}/data"
                # QoS 1 = "at least once" -- appropriate for structural
                # monitoring data where you don't want silent drops.
                client.publish(topic, json.dumps(reading), qos=1)
                print(f"[{topic}] {reading}")
            time.sleep(PUBLISH_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nStopping publisher.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
