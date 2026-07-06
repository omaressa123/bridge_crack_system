"""
Sensor configuration file.

Set USE_FAKE_SENSORS to True to use software-generated fake sensor readings
(perfect for testing before buying physical hardware). Set to False later
to read from real sensors (ADC, I2C, etc.) on a Raspberry Pi/ESP32.
"""

# 🔧 Toggle this flag to switch between fake and real sensors
USE_FAKE_SENSORS = True  # Change to False when hardware is ready
