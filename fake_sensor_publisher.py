"""
Fake sensor publisher.

Simulates one or more bridge sensor units publishing readings over MQTT,
exactly as a real ESP32/Raspberry Pi + sensor kit would once you buy the
hardware. Swap the `generate_reading()` function for real sensor reads
later -- nothing else in this file, or in the backend, needs to change.

Usage:
    pip install paho-mqtt
    python fake_sensor_publisher.py
"""

import json
import random
import time

import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883

# Simulate readings for these bridge IDs. Add more to simulate more bridges.
BRIDGE_IDS = ["bridge_1", "bridge_2"]

PUBLISH_INTERVAL_SECONDS = 5

# Chance that a reading is an artificial "spike", to test your alert logic
# (matches the thresholds used in calculate_bridge_severity: vibration > 1.5g,
# moisture > 80%, strain > 700 microstrain).
SPIKE_PROBABILITY = 0.05


def generate_reading() -> dict:
    """Build one fake sensor reading. Replace this with real GPIO/I2C reads
    once you have physical sensors -- keep the same dict shape."""
    if random.random() < SPIKE_PROBABILITY:
        return {
            "temperature": round(random.uniform(35, 48), 1),
            "moisture": round(random.uniform(80, 99), 1),
            "vibration": round(random.uniform(1.5, 3.0), 2),
            "strain": round(random.uniform(700, 950), 1),
        }
    return {
        "temperature": round(random.uniform(20, 34), 1),
        "moisture": round(random.uniform(10, 79), 1),
        "vibration": round(random.uniform(0.1, 1.4), 2),
        "strain": round(random.uniform(0, 699), 1),
    }


def main():
    client = mqtt.Client(client_id="fake_sensor_publisher")
    client.connect(BROKER_HOST, BROKER_PORT)
    client.loop_start()

    print(f"Publishing fake readings for {BRIDGE_IDS} every {PUBLISH_INTERVAL_SECONDS}s "
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
