# MQTT sensor simulation for bridge_crack_system

Simulate real sensors over MQTT before buying any hardware. Same code
path as production: swap the fake publisher for a real ESP32/Pi later,
nothing else changes.

## Files in this folder

- `docker-compose.yml` + `mosquitto.conf` — a local MQTT broker (Mosquitto)
- `fake_sensor_publisher.py` — pretends to be sensors, publishes readings
- `mqtt_ingest.py` — drop into `backend/`, subscribes and feeds your real DB + dashboard

## 1. Start the broker

```bash
cd mqtt_simulation
docker compose up -d
```

Check it's running:
```bash
docker ps   # should show bridge_mqtt_broker
```

## 2. Install the MQTT client library

```bash
pip install paho-mqtt --break-system-packages
```//(or just `pip install paho-mqtt` in your own environment)

## 3. Wire the ingest module into your backend

1. Copy `mqtt_ingest.py` into `bridge_crack_system/backend/`.
2. Open `backend/main.py` and add the three snippets shown in the
   comment block at the bottom of `mqtt_ingest.py`:
   - import and call `start_mqtt_listener(...)` on startup
   - a `connected_websockets` list + `broadcast_to_dashboards` function
   - simplify your existing `/ws` handler to just hold the connection open
     instead of generating random data every 60s
3. Start your backend as usual:
   ```bash
   python main.py
   ```
   You should see:
   ```
   [mqtt_ingest] connected to broker, rc=0
   [mqtt_ingest] subscribed to sensors/+/data
   [mqtt_ingest] listener thread started
   ```

## 4. Run the fake sensor publisher

In a separate terminal:
```bash
python fake_sensor_publisher.py
```

You'll see readings being published every 5 seconds:
```
[sensors/bridge_1/data] {'temperature': 27.3, 'moisture': 41.2, 'vibration': 0.6, 'strain': 210.4, ...}
```

And in your backend terminal:
```
[mqtt_ingest] saved reading for bridge_id=1
```

## 5. Open the React dashboard

```bash
npm run dev
```

Your dashboard should now update live from the fake sensor stream — same
UI, same charts, same alert thresholds — but the data is arriving exactly
the way it will once real hardware is plugged in.

## 6. When you buy real sensors

Take `fake_sensor_publisher.py`, run it on the ESP32/Raspberry Pi instead
of your laptop, and replace `generate_reading()` with real sensor reads
(the exact GPIO/I2C code is already in SENSOR_GUIDE.md). Point it at the
same broker IP. Nothing in the backend or frontend needs to change.

## Testing alerts before buying hardware

`fake_sensor_publisher.py` has a `SPIKE_PROBABILITY` (default 5%) that
occasionally generates out-of-range values matching your existing
severity thresholds (vibration > 1.5g, moisture > 80%, strain > 700
microstrain). Raise it temporarily to 0.5 to trigger alerts quickly and
confirm your dashboard's warning states actually fire.
