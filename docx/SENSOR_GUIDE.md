# 📡 SENSOR GUIDE - Bridge Crack Detection System

## 🎯 Sensor Overview

Your system uses **4 types of sensors** to monitor bridge health:

```
┌─────────────────────────────────────────────┐
│  Bridge Structural Health Monitoring        │
├─────────────────────────────────────────────┤
│                                              │
│  1. 📊 ACCELEROMETER    → Vibration         │
│  2. 💧 MOISTURE SENSOR   → Water damage      │
│  3. 🌡️  TEMPERATURE      → Thermal stress   │
│  4. 📏 STRAIN GAUGE      → Structural stress│
│                                              │
└─────────────────────────────────────────────┘
```

---

## 1️⃣ ACCELEROMETER (Vibration Detection)

### **Why Use It?**
- Detects vehicle-induced vibrations
- Identifies structural resonance
- Early warning for instability
- Monitors traffic patterns

### **Sensor: MPU6050**

```
MPU6050 Triple Axis Accelerometer + Gyroscope
┌────────────────────────────┐
│  Specifications:           │
├────────────────────────────┤
│ Range: ±2g to ±16g        │
│ Resolution: 16-bit        │
│ Output: Digital (I2C)     │
│ Supply Voltage: 3.3V-5V   │
│ Current: 3.5 mA           │
│ Sampling Rate: 8kHz max   │
└────────────────────────────┘
```

### **Pin Connections (to Raspberry Pi)**
```
MPU6050              Raspberry Pi
───────              ─────────────
VCC          ────→   3.3V (Pin 1)
GND          ────→   GND (Pin 6)
SCL (Clock)  ────→   GPIO 3 (I2C SCL)
SDA (Data)   ────→   GPIO 2 (I2C SDA)
```

### **Python Code**
```python
import board
import busio
import adafruit_mpu6050

i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_mpu6050.MPU6050(i2c)

# Read acceleration (m/s²)
acceleration = sensor.acceleration
print(f"X: {acceleration[0]}, Y: {acceleration[1]}, Z: {acceleration[2]}")

# Read gyroscope (rad/s)
gyro = sensor.gyro
```

### **What It Measures**
- **X-axis**: Side-to-side motion
- **Y-axis**: Forward-backward motion
- **Z-axis**: Up-down motion (vertical)

### **Typical Readings**
```
Normal Traffic:    0.2 - 0.5 g
Heavy Traffic:     0.5 - 1.0 g
Unusual Vibration: > 1.5 g (ALERT!)
```

### **Cost in Egypt**
- ✅ **150-200 EGP** per sensor
- Quantity discount available

---

## 2️⃣ MOISTURE SENSOR (Water Damage Detection)

### **Why Use It?**
- Detects water infiltration
- Prevents rust/corrosion
- Identifies leaks early
- Monitors rainfall impact

### **Sensor: Capacitive Soil Moisture Sensor**

```
Capacitive Moisture Sensor
┌────────────────────────────┐
│  Specifications:           │
├────────────────────────────┤
│ Range: 0-100% (soil)       │
│ Accuracy: ±3%             │
│ Output: Analog (0-5V)     │
│ Supply: 5V                │
│ Current: 5mA              │
│ Response Time: < 1 sec    │
│ Durability: High (no corr)│
└────────────────────────────┘
```

### **Pin Connections (to Raspberry Pi via ADC)**
```
Moisture Sensor      Raspberry Pi (via MCP3008 ADC)
───────────────      ─────────────────────────────
VCC         ────→   5V
GND         ────→   GND
AOUT        ────→   ADC Channel 0
DOUT        ────→   GPIO (optional, threshold)
```

### **Python Code (with MCP3008 ADC)**
```python
import busio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# Setup SPI and ADC
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D8)
mcp = MCP.MCP3008(spi, cs)
channel = AnalogIn(mcp, MCP.P0)

# Read moisture
moisture_voltage = channel.voltage
# Convert to percentage (0-100%)
moisture_percent = (moisture_voltage / 3.3) * 100
print(f"Moisture: {moisture_percent:.1f}%")
```

### **Calibration**
```python
# Dry air: 0V = 0%
# Wet: 3.3V = 100%

def calibrate_moisture():
    print("Place sensor in DRY environment, press Enter...")
    input()
    dry_value = channel.voltage
    
    print("Place sensor in WET environment, press Enter...")
    input()
    wet_value = channel.voltage
    
    return dry_value, wet_value

dry, wet = calibrate_moisture()

def get_moisture_percent():
    voltage = channel.voltage
    percent = ((voltage - dry) / (wet - dry)) * 100
    return max(0, min(100, percent))
```

### **Typical Readings**
```
Dry Concrete:  10-20%
Normal:        30-50%
After Rain:    60-80%
Saturated:     90-100% (ALERT!)
```

### **Cost in Egypt**
- ✅ **200-250 EGP** per sensor
- Capacitive type (better than resistive)

---

## 3️⃣ TEMPERATURE SENSOR (Thermal Stress Monitoring)

### **Why Use It?**
- Detects thermal expansion/contraction
- Monitors temperature stress on concrete
- Early warning for freeze-thaw damage
- Corrosion rate correlation

### **Sensor: DS18B20 (Recommended) or DHT22**

```
DS18B20 Digital Temperature Sensor
┌────────────────────────────┐
│  Specifications:           │
├────────────────────────────┤
│ Range: -55°C to +125°C     │
│ Accuracy: ±0.5°C          │
│ Output: Digital (1-Wire)   │
│ Supply: 3.3V-5V           │
│ Current: 4mA (max)        │
│ Resolution: 12-bit        │
│ Response Time: 750ms      │
└────────────────────────────┘
```

### **Pin Connections**
```
DS18B20              Raspberry Pi
────────             ─────────────
VCC         ────→   3.3V / 5V
GND         ────→   GND
DQ (Signal) ────→   GPIO 4 (with 4.7K pullup to VCC)

Note: Pullup resistor is REQUIRED for 1-Wire protocol
```

### **Pullup Resistor Circuit**
```
3.3V
  │
  ├─[4.7kΩ]─┬─── to DQ (GPIO 4)
  │         │
  └─────────┴─── to all DS18B20 sensors
```

### **Python Code**
```python
import os
import glob
import time

# 1-Wire setup
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

def read_temp():
    device_file = '/sys/bus/w1/devices/28-*/w1_slave'
    files = glob.glob(device_file)
    
    if not files:
        print("No temperature sensor found!")
        return None
    
    with open(files[0], 'r') as f:
        lines = f.readlines()
    
    if lines[0].strip()[-3:] == 'YES':
        temp_pos = lines[1].find('t=')
        if temp_pos != -1:
            temp_string = lines[1][temp_pos+2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c
    
    return None

# Read every 60 seconds
while True:
    temp = read_temp()
    print(f"Temperature: {temp:.2f}°C")
    time.sleep(60)
```

### **Typical Readings**
```
Winter (Egypt): 15-25°C
Summer (Egypt): 35-45°C
On Black Surface: +5 to +10°C higher
Thermal Stress Alert: > 50°C or < 5°C
```

### **Cost in Egypt**
- ✅ **100-150 EGP** per sensor
- DS18B20 waterproof version available

---

## 4️⃣ STRAIN GAUGE (Structural Stress)

### **Why Use It?**
- Measures concrete compression/tension
- Detects structural deformation
- Early warning for load-bearing issues
- Validates structural integrity

### **Sensor: Electrical Strain Gauge (350Ω)**

```
Strain Gauge + Load Cell Amplifier (HX711)
┌────────────────────────────┐
│  Specifications:           │
├────────────────────────────┤
│ Type: 4-Wire (Wheatstone) │
│ Resistance: 350Ω          │
│ GF (Gauge Factor): 2.0    │
│ Output: Very small voltage │
│ Needs Amplifier: HX711    │
│ Supply: 5V (amplifier)    │
│ Output: Digital SPI       │
└────────────────────────────┘
```

### **System Setup**

```
Strain Gauge (4 wires)
     │
     └──→ HX711 Load Cell Amplifier
            │
            ├─ VCC  → 5V
            ├─ GND  → GND
            ├─ DT   → GPIO 5
            └─ SCK  → GPIO 6
```

### **Installation on Bridge**

```
Concrete Surface
     │
     ├─ [Strain Gauge] ← Mounted on concrete
     │        │
     └─ [Adhesive] ← Use epoxy or mounting brackets
     
Measures compression/tension in concrete
```

### **Python Code (with HX711)**
```python
import time
from hx711 import HX711

# Initialize HX711
hx = HX711(dout_pin=5, pd_sck_pin=6)

# Calibration (must do first!)
def calibrate():
    hx.reset()
    time.sleep(1)
    hx.tare()  # Set to zero with no load
    print("Calibrated!")

# Reading strain
def read_strain():
    raw_value = hx.read()
    # Calibration factor depends on your setup
    # Typically 100-1000 for strain gauges
    calibration_factor = 250
    strain = raw_value / calibration_factor
    return strain

calibrate()

while True:
    strain = read_strain()
    print(f"Strain: {strain} μ (micro-strain)")
    time.sleep(60)
```

### **Typical Readings**
```
No Load:           0 μ (micro-strain)
Normal Load:       100-300 μ
Heavy Traffic:     300-500 μ
Stress Alert:      > 700 μ (ALERT!)
```

### **Cost in Egypt**
- ✅ **300-400 EGP** for strain gauge + HX711 amplifier

---

## 🔧 HARDWARE BILL OF MATERIALS (BOM)

```
Component                  | Qty | Cost (EGP) | Total
───────────────────────────┼─────┼────────────┼──────
1. MPU6050 Accelerometer   │  2  │   150      │  300
2. Capacitive Moisture     │  2  │   200      │  400
3. DS18B20 Temperature     │  2  │   100      │  200
4. Strain Gauge + HX711    │  2  │   350      │  700
5. Raspberry Pi 4 (4GB)    │  1  │  1500      │ 1500
6. MCP3008 ADC (8-channel) │  1  │   80       │   80
7. Cables & Connectors     │  -  │   400      │  400
8. Pullup Resistors (4.7K) │ 10  │    20      │  200
9. Weatherproof Box        │  1  │   800      │  800
10. Power Supply (5V/3A)   │  1  │   300      │  300
11. USB SD Card (64GB)     │  1  │   150      │  150
───────────────────────────┴─────┴────────────┴──────
TOTAL SENSOR COST:                          4,930 EGP
```

---

## 🔌 COMPLETE WIRING DIAGRAM

```
Raspberry Pi 4
┌─────────────────────────────────────┐
│  GPIO Pins & I2C Bus                │
├─────────────────────────────────────┤
│                                     │
│  3.3V ──────┬─ MPU6050 VCC         │
│             └─ DS18B20 VCC         │
│                                     │
│  GND ───────┬─ MPU6050 GND         │
│             ├─ All Sensors GND     │
│             └─ Power Supply GND    │
│                                     │
│  GPIO 2 ────┬─ MPU6050 SDA (I2C)  │
│  GPIO 3 ────├─ MPU6050 SCL (I2C)  │
│             │                      │
│  GPIO 4 ────┼─ DS18B20 DQ         │
│  GPIO 5 ────┼─ HX711 DT (Strain)  │
│  GPIO 6 ────┼─ HX711 SCK          │
│             │                      │
│  5V ────────┴─ MCP3008 VCC         │
│  GND ────────── MCP3008 GND        │
│                                     │
│  SPI ────────── MCP3008 (Moisture) │
│                                     │
└─────────────────────────────────────┘
```

---

## 📊 DATA COLLECTION INTERVALS

```
Sensor              | Frequency | Why
────────────────────┼───────────┼─────────────────────
Accelerometer (Vibration) | 1000 Hz   | High frequency for vibration analysis
Temperature         | Every 60s | Slow changes
Moisture           | Every 60s | Gradual change
Strain Gauge       | Every 60s | Structural changes are slow
────────────────────┴───────────┴─────────────────────
```

---

## 🛡️ WEATHERPROOFING

All sensors must be protected from rain/UV:

### **Enclosure Setup**
```
IP67 Waterproof Box
┌──────────────────────────┐
│                          │
│  ┌─ RPi inside box      │
│  ├─ All circuits here   │
│  └─ Temperature stable  │
│                          │
│  Sensor cables → Exit via │
│  sealed cable glands     │
│                          │
│  Accelerometer → Bridge  │
│  Moisture → Bridge       │
│  Strain → Bridge         │
│  Temperature → Bridge    │
│                          │
└──────────────────────────┘
```

### **Sensor Protection**
```
Each Sensor Needs:
├─ Epoxy coating (waterproof)
├─ Silicone sealant (joints)
├─ UV-resistant mounting
└─ Stainless steel hardware (corrosion-proof)
```

---

## 🔄 DATA FUSION LOGIC

Your app combines all 4 sensors:

```python
def calculate_bridge_severity(acceleration, moisture, temperature, strain):
    """
    Combines 4 sensors to predict overall bridge health
    """
    
    severity_score = 0
    
    # 1. Vibration Analysis (30% weight)
    if acceleration > 1.5:  # High vibration
        severity_score += 30
    elif acceleration > 0.8:
        severity_score += 15
    
    # 2. Moisture Analysis (25% weight)
    if moisture > 80:  # High moisture
        severity_score += 25
    elif moisture > 60:
        severity_score += 12
    
    # 3. Thermal Stress (20% weight)
    temp_diff = abs(current_temp - baseline_temp)
    if temp_diff > 25:  # Large change
        severity_score += 20
    elif temp_diff > 15:
        severity_score += 10
    
    # 4. Structural Stress (25% weight)
    if strain > 700:  # High strain
        severity_score += 25
    elif strain > 400:
        severity_score += 12
    
    # Final severity (0-100)
    return min(100, severity_score)

# Map to levels
def get_severity_level(score):
    if score < 33:
        return "SAFE ✅" 
    elif score < 67:
        return "MONITOR ⚠️"
    else:
        return "URGENT REPAIR 🚨"
```

---

## 🧪 SENSOR CALIBRATION PROCEDURE

### **Step 1: Accelerometer Calibration**
```python
# MPU6050 has built-in calibration
# Run at startup with sensor at rest
mpu.calibrate()
print("Accelerometer calibrated")
```

### **Step 2: Moisture Calibration**
```python
# Mentioned above - dry vs wet comparison
dry_value, wet_value = calibrate_moisture()
```

### **Step 3: Temperature Baseline**
```python
# Record baseline temperature on first run
baseline_temp = read_temp()
# Use this to calculate thermal stress
thermal_stress = abs(current_temp - baseline_temp)
```

### **Step 4: Strain Gauge Calibration**
```python
# Must calibrate with known weights
# Place known load and calculate factor

def calibrate_strain():
    print("Remove all weight, press Enter...")
    input()
    zero_value = hx.read()
    
    print("Place 10kg weight, press Enter...")
    input()
    ten_kg_value = hx.read()
    
    calibration_factor = (ten_kg_value - zero_value) / 10
    return calibration_factor

cal_factor = calibrate_strain()
```

---

## 📈 SENSOR RELIABILITY

```
Sensor              | MTBF      | Reliability | Notes
────────────────────┼───────────┼─────────────┼─────────
Accelerometer       | 50,000 h  | Very High   | ✅ Industrial
Moisture (Cap)      | 30,000 h  | High        | ✅ Durable
Temperature (DS)    | 100,000 h | Very High   | ✅ Best
Strain Gauge        | 20,000 h  | Medium      | ⚠️ Needs care
────────────────────┴───────────┴─────────────┴─────────
```

---

## 🚨 ALERT THRESHOLDS

Your app will trigger alerts when:

| Sensor | Alert Threshold | Meaning |
|--------|-----------------|---------|
| **Vibration** | > 1.5 g | Abnormal movement |
| **Moisture** | > 80% | Water infiltration detected |
| **Temperature** | ±25°C from baseline | Thermal stress |
| **Strain** | > 700 μ | Excessive deformation |

---

## 💾 DATA STORAGE (Per Bridge)

```
Daily data:
- Accelerometer: 86,400 readings/day = 350 KB
- Temperature: 1,440 readings/day = 10 KB
- Moisture: 1,440 readings/day = 10 KB
- Strain: 1,440 readings/day = 10 KB

Total per bridge/day: ~380 KB
Per month: ~11 MB
Per year: ~140 MB (very small)

64GB SD Card can store:
- 450+ years of data for 1 bridge
- Or 5+ years for 100 bridges
```

---

## 🎯 WHERE TO BUY (Egypt)

### **Online Shops**
- Jumia Egypt
- Amazon Egypt
- Local electronics shops (Cairo)

### **Local Suppliers**
- Mahmoud Electronics (Cairo)
- Tech Store Alexandria
- Robotics shops

### **Import Options**
- AliExpress (5-10 days shipping)
- Amazon Global (higher cost)
- Direct from manufacturers

---

## ⚙️ INSTALLATION TIPS

1. **Mounting Accelerometer**
   - Mount rigidly to bridge deck
   - Use epoxy for permanent attachment
   - Avoid moving parts

2. **Moisture Sensor**
   - Place in moisture-prone areas
   - Near joints and cracks
   - Keep probe clean

3. **Temperature Sensor**
   - Mount on bridge surface
   - Measure concrete, not air
   - Use thermal paste for contact

4. **Strain Gauge**
   - Requires professional installation
   - Use epoxy adhesive
   - Keep wires protected
   - Multiple gauges for redundancy

---

## 🔍 TROUBLESHOOTING SENSORS

### **Accelerometer not reading**
```
Check: I2C connection, pull-up resistors, address (0x68)
```

### **Moisture sensor stuck at high/low**
```
Solution: Recalibrate, check MCP3008 voltage, clean probe
```

### **Temperature reading wrong**
```
Check: Sensor contact with surface, calibration, 1-Wire protocol
```

### **Strain gauge drifting**
```
Solution: Recalibrate, check amplifier, ensure stable power
```

---

## ✅ SENSOR SETUP CHECKLIST

- [ ] All sensors sourced locally
- [ ] MPU6050 wired to I2C (GPIO 2, 3)
- [ ] DS18B20 wired to GPIO 4 with 4.7K pullup
- [ ] MCP3008 ADC wired for moisture sensor
- [ ] HX711 amplifier wired for strain gauge
- [ ] All power/GND connections verified
- [ ] Weatherproof enclosure prepared
- [ ] Cables protected from elements
- [ ] Sensor calibration script ready
- [ ] Test data collection running
- [ ] Database tables created
- [ ] Data transmission to app verified

---

## 📚 SENSOR LIBRARIES FOR PYTHON

```bash
# Install on Raspberry Pi:
pip install adafruit-circuitpython-mpu6050
pip install adafruit-circuitpython-mcp3xxx
pip install hx711
pip install RPi.GPIO
pip install board busio
```

---

## 🎬 DEMO: Simulated Sensor Data

Your React app comes with **mock sensor data**:

```javascript
// Dashboard shows:
Temperature: 32°C
Moisture: 45%
Vibration: 0.8g
Strain: 120μ

// After backend connects, replaces with REAL data from:
// /sensors/data?bridge_id=1
```

---

## 🏁 NEXT STEPS

1. ✅ Review sensor specifications
2. ✅ Order sensors (BOM provided)
3. ✅ Practice wiring on breadboard
4. ✅ Write sensor reading code
5. ✅ Calibrate each sensor
6. ✅ Test data collection
7. ✅ Integrate with React app
8. ✅ Deploy to bridge

---

**Questions about sensors? Refer to:**
- Sensor datasheets (available online)
- Adafruit guides (https://learn.adafruit.com)
- RPi documentation (https://www.raspberrypi.com/documentation/)

---

*SensorX Challenge 2026 - Bridge Crack Detection System*
