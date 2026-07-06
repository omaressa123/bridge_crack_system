"""
Fake sensor implementations.

Each sensor has a read() method that returns a simulated reading with optional
spikes for testing alert logic. When you buy physical hardware, you can replace
this with real_sensors.py without changing any other code.
"""

import random

# Global spike probability for test alerts
SPIKE_PROBABILITY = 0.05


class FakeTemperatureSensor:
    def __init__(self, min_val=20, max_val=34, spike_min=35, spike_max=48):
        self.min_val = min_val
        self.max_val = max_val
        self.spike_min = spike_min
        self.spike_max = spike_max

    def read(self) -> float:
        if random.random() < SPIKE_PROBABILITY:
            return round(random.uniform(self.spike_min, self.spike_max), 1)
        return round(random.uniform(self.min_val, self.max_val), 1)


class FakeMoistureSensor:
    def __init__(self, min_val=10, max_val=79, spike_min=80, spike_max=99):
        self.min_val = min_val
        self.max_val = max_val
        self.spike_min = spike_min
        self.spike_max = spike_max

    def read(self) -> float:
        if random.random() < SPIKE_PROBABILITY:
            return round(random.uniform(self.spike_min, self.spike_max), 1)
        return round(random.uniform(self.min_val, self.max_val), 1)


class FakeVibrationSensor:
    def __init__(self, min_val=0.1, max_val=1.4, spike_min=1.5, spike_max=3.0):
        self.min_val = min_val
        self.max_val = max_val
        self.spike_min = spike_min
        self.spike_max = spike_max

    def read(self) -> float:
        if random.random() < SPIKE_PROBABILITY:
            return round(random.uniform(self.spike_min, self.spike_max), 2)
        return round(random.uniform(self.min_val, self.max_val), 2)


class FakeStrainSensor:
    def __init__(self, min_val=0, max_val=699, spike_min=700, spike_max=950):
        self.min_val = min_val
        self.max_val = max_val
        self.spike_min = spike_min
        self.spike_max = spike_max

    def read(self) -> float:
        if random.random() < SPIKE_PROBABILITY:
            return round(random.uniform(self.spike_min, self.spike_max), 1)
        return round(random.uniform(self.min_val, self.max_val), 1)


# Initialize sensor instances for easy import
temp_sensor = FakeTemperatureSensor()
moisture_sensor = FakeMoistureSensor()
accel_sensor = FakeVibrationSensor()
strain_sensor = FakeStrainSensor()
