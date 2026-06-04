# Boca Printer Paper Monitor - Hardware Wiring Guide

## Overview

This document provides detailed wiring instructions for connecting the reflective light sensor and optional LED indicators to the Raspberry Pi.

**IMPORTANT SAFETY NOTES:**
- Always disconnect power before wiring or modifying connections
- Double-check all connections before applying power
- Use proper resistors to protect LEDs and GPIO pins
- Never exceed 3.3V on GPIO pins
- Use a quality power supply (minimum 2A recommended)

---

## Component Specifications

### Reflective Light Sensor (Example: E18-D80NK)

**Specifications:**
- Operating Voltage: 5V typical (but 3.3V compatible with pull-up)
- Output Type: NPN open-collector (logic LOW when reflection detected)
- Detection Range: 3-8 cm (adjustable with potentiometer)
- Current Draw: ~35-40 mA (5V)

**Pin Configuration:**
- Pin 1 (Brown): Anode (+V)
- Pin 2 (Black): Cathode (GND)
- Pin 3 (Blue): Output (to GPIO pin)

### Raspberry Pi GPIO Reference

**GPIO Pin Locations:**
- GPIO 17: Pin 11 (40-pin header)
- GPIO 27: Pin 13
- GPIO 22: Pin 15
- 3.3V: Pins 1, 17
- 5V: Pins 2, 4
- GND: Pins 6, 9, 14, 20, 25, 30, 34, 39

---

## Wiring Diagrams

### DIAGRAM 1: Reflective Light Sensor (GPIO 17)

```
Raspberry Pi 3.3V Supply
         │
         │
      [Pull-up Resistor]     ← Optional: 10kΩ to 47kΩ
         │                        (often internal in sensor module)
         ├──────────────────────────┬──────────────────────┐
         │                          │                      │
    [Sensor Module]          GPIO 17 (Pin 11)         [GND]
      ┌──────────────┐            │                       │
      │    SENSOR    │            │                    [GND Pin]
      │              │            │
      │ Pin1 (+5V)───┼──[+5V]─────┤
      │              │
      │ Pin2 (GND)───┼──[GND]─────┘
      │              │
      │ Pin3 (OUT)───┼──────[Blue Wire]─────→ GPIO 17
      └──────────────┘

Output Logic:
  Paper Present  → NO reflection    → GPIO = LOW  (0)
  Paper Out      → Reflection found → GPIO = HIGH (1)
```

### DIAGRAM 2: LED Indicators (Optional)

#### Green LED (Paper OK) - GPIO 27

```
Raspberry Pi 3.3V
         │
         │
    GPIO 27 (Pin 13)
         │
         │
      [330Ω Resistor]  ← REQUIRED to protect GPIO
         │
    ────[LED]──────────
      (Longer leg)
         │
      [GND Pin 6]
      
Light ON when GPIO 27 = HIGH (paper OK)
```

#### Red LED (Paper Out) - GPIO 22

```
Raspberry Pi 3.3V
         │
         │
    GPIO 22 (Pin 15)
         │
         │
      [330Ω Resistor]  ← REQUIRED to protect GPIO
         │
    ────[LED]──────────
      (Longer leg)
         │
      [GND Pin 20]
      
Light ON when GPIO 22 = HIGH (paper out)
```

---

## Complete Physical Wiring Layout

### 40-Pin Raspberry Pi GPIO Header

```
PIN LAYOUT (looking at Pi with USB ports facing down):

PIN#  │ FUNCTION        │ PIN#  │ FUNCTION
──────┼─────────────────┼───────┼─────────────────
  1   │ 3.3V            │   2   │ 5V
  3   │ GPIO 2 (SDA)    │   4   │ 5V
  5   │ GPIO 3 (SCL)    │   6   │ GND
  7   │ GPIO 4          │   8   │ GPIO 14 (TXD)
  9   │ GND             │  10   │ GPIO 15 (RXD)
 11   │ GPIO 17 ★       │  12   │ GPIO 18 (PWM)
 13   │ GPIO 27 ★       │  14   │ GND
 15   │ GPIO 22 ★       │  16   │ GPIO 23
 17   │ 3.3V            │  18   │ GPIO 24
 19   │ GPIO 10 (MOSI)  │  20   │ GND
 21   │ GPIO 9 (MISO)   │  22   │ GPIO 25
 23   │ GPIO 11 (SCLK)  │  24   │ GPIO 8 (CE0)
 25   │ GND             │  26   │ GPIO 7 (CE1)
 27   │ GPIO 0 (ID_SD)  │  28   │ GPIO 1 (ID_SC)
 29   │ GPIO 5          │  30   │ GND
 31   │ GPIO 6          │  32   │ GPIO 12 (PWM)
 33   │ GPIO 13 (PWM)   │  34   │ GND
 35   │ GPIO 19 (PWM)   │  36   │ GPIO 16
 37   │ GPIO 26         │  38   │ GPIO 20
 39   │ GND             │  40   │ GPIO 21

★ = Pins used in this project
```

---

## Step-by-Step Wiring Instructions

### Prerequisites

- Raspberry Pi (powered off)
- Jumper wires (various colors - red for +, black for -, colored for signals)
- Breadboard or terminal blocks (for easy connections)
- Multimeter (for testing connections)

### Sensor Connection

**Step 1: Prepare Sensor**
1. Identify sensor module pins (or buy pre-made module with JST connector)
2. If using raw sensor, solder wires to pins (use heat shrink tubing)
3. Label wires clearly (VCC, GND, OUT)

**Step 2: Connect to Raspberry Pi**
1. Connect Sensor VCC (brown) to Raspberry Pi 5V (Pin 2 or 4)
   - Why 5V? Sensor module regulates to 3.3V output
2. Connect Sensor GND (black) to Raspberry Pi GND (Pin 6, 9, 14, 20, 25, 30, 34, or 39)
3. Connect Sensor OUT (blue) to GPIO 17 (Pin 11)

**Step 3: Verify Connections**
- Use multimeter to verify continuity
- Check voltage levels:
  - VCC pin: ~5V
  - GND pin: 0V
  - OUT pin (no signal): ~3.3V (pulled high via pull-up)

### LED Connection (Optional)

**Step 4: Green LED (Paper OK)**
1. Connect GPIO 27 (Pin 13) to 330Ω resistor
2. Connect resistor to long leg of green LED
3. Connect short leg of green LED to GND (Pin 6, 14, 20, 25, 30, 34, or 39)

**Step 5: Red LED (Paper Out)**
1. Connect GPIO 22 (Pin 15) to 330Ω resistor
2. Connect resistor to long leg of red LED
3. Connect short leg of red LED to GND (Pin 20)

**Step 6: Verify LED Polarity**
- Long leg = Anode (+) - connects to GPIO through resistor
- Short leg = Cathode (-) - connects to GND
- Incorrect polarity = LED won't light up

---

## Breadboard Layout Example

```
RASPBERRY PI ┌──────────┐
GPIO Header  │ BREADBOARD │
             └──────────┘
             
    3.3V ─────┬──────[┬]─────┬───────────┬───────────┐
              │      │       │           │           │
             GND     [Pull-up]         [330Ω]      [330Ω]
              │      Resistor          (Green)     (Red)
              │      (if needed)          │           │
              │      │                    │           │
             [6]   [17]               [27 LED]   [22 LED]
              │      │                    │           │
             GND   [Sensor]              GND         GND
                     OUT
```

---

## Advanced Configuration

### Adjusting Sensor Sensitivity

**Via Hardware Potentiometer:**
1. Most sensor modules have a potentiometer (variable resistor)
2. Rotate clockwise to increase sensitivity (shorter detection range)
3. Rotate counter-clockwise to decrease sensitivity (longer detection range)
4. Target: Detect when paper is approximately 2-3cm below sensor

**Via Software Debouncing:**
- Edit `printer_monitor.py`
- Adjust `DEBOUNCE_COUNT` (default: 5)
- Higher = more stable but slower response (good for false positives)
- Lower = faster response but more susceptible to noise

### Using External Pull-Up Resistor

If your sensor module doesn't have internal pull-up:

```
3.3V
 │
[10kΩ resistor]  ← Add 10-47kΩ pull-up
 │
 ├──────────→ GPIO 17 (and to sensor output)
 │
[Sensor OUT]
```

### Long Cable Runs (>1 meter)

For runs longer than 1 meter:
1. Use shielded twisted-pair cable
2. Ground the shield at the Raspberry Pi end only
3. Reduce sensor read interval (slower polling)
4. Increase DEBOUNCE_COUNT for stability

---

## Testing Connections

### Visual Inspection Checklist

- [ ] All power connections (5V, 3.3V) are firm
- [ ] All GND connections are secure
- [ ] Signal wire (blue) is connected to GPIO 17 only
- [ ] LED long leg connects to GPIO through resistor
- [ ] LED short leg connects to GND
- [ ] No loose wires touching other components
- [ ] No connections crossing over unpowered areas

### Multimeter Testing

```bash
# With Raspberry Pi powered off:

1. Check for shorts:
   - Voltage between 5V and GND: Should read ~5V
   - Voltage between 3.3V and GND: Should read ~3.3V
   - Continuity from GPIO 17 to sensor output
   
2. Check LED polarity:
   - Use ohm meter (resistance mode)
   - Forward bias: Low resistance (~∞ to low ohms)
   - Reverse bias: No continuity
   
3. Check resistor values:
   - 330Ω resistor: Should read ~330Ω ±5%
   - Pull-up resistor: Should read 10-47kΩ
```

### Software Testing

```bash
# With Raspberry Pi powered on and service running:

# Test GPIO 17 sensor reading
gpio -g read 17
# Should alternate between 0 (paper present) and 1 (paper out)

# Test GPIO 27 (green LED)
gpio -g mode 27 out
gpio -g write 27 1  # LED on
gpio -g write 27 0  # LED off

# Test GPIO 22 (red LED)
gpio -g mode 22 out
gpio -g write 22 1  # LED on
gpio -g write 22 0  # LED off

# Monitor sensor values in real-time
watch -n 0.5 'gpio -g read 17'
```

---

## Troubleshooting

### Sensor Not Detecting

**Problem:** Always returns "PAPER_OK" even with no paper

**Possible Causes:**
1. Sensor not powered (check 5V supply)
2. Output wire disconnected or loose
3. Wrong GPIO pin configured
4. Sensor pointing wrong direction (should face down toward backing plate)

**Solutions:**
1. Verify 5V power with multimeter
2. Re-seat all connections
3. Check GPIO pin matches SENSOR_PIN in config
4. Reorient sensor to face reflective surface

### LED Not Lighting

**Problem:** LEDs not indicating status

**Possible Causes:**
1. LED polarity reversed (long leg must connect to GPIO side)
2. Missing resistor (LED may be protected but excessive current)
3. GPIO pin not toggling correctly
4. Loose connections

**Solutions:**
1. Check LED orientation: long leg = anode (+)
2. Verify 330Ω resistor is present
3. Test GPIO manually: `gpio -g write 27 1`
4. Re-check all connections

### Intermittent Readings

**Problem:** Sensor values fluctuate wildly

**Possible Causes:**
1. Loose or noisy connection
2. Insufficient pull-up resistance
3. Environmental light interference
4. Long cable runs without shielding

**Solutions:**
1. Tighten all connections
2. Add/increase pull-up resistor
3. Add shield/cover around sensor
4. Use shielded cable and increase DEBOUNCE_COUNT

---

## Pin Assignment Summary

| Component | GPIO | Pin # | Notes |
|-----------|------|-------|-------|
| Reflective Sensor | 17 | 11 | Input, 3.3V logic |
| Green LED | 27 | 13 | Output, needs 330Ω resistor |
| Red LED | 22 | 15 | Output, needs 330Ω resistor |
| GND | - | 6,9,14,20,25,30,34,39 | Use any |
| 3.3V | - | 1,17 | Sensor module output voltage |
| 5V | - | 2,4 | Sensor module power |

---

## Component Purchasing Reference

### Recommended Sensors

1. **E18-D80NK** (Recommended)
   - Visible red light reflective sensor
   - 3-8cm detection range (adjustable)
   - Long lifespan, weatherproof

2. **QTR-8RC**
   - Multiple sensors on one module
   - 3.3V compatible
   - Good for complex sensing

3. **Sharp GP2Y0A51SF00F**
   - Infrared analog distance sensor
   - Wider detection range
   - More complex signal processing

### Compatible LED Indicators

- **Resistor Color Codes for 330Ω:**
  - Orange, Orange, Brown = 330Ω
  - Verify with multimeter

---

## Maintenance and Care

### Regular Checks

- Monthly: Verify sensor is clean (no dust/dirt on lens)
- Quarterly: Check all connections remain firm
- Annually: Replace sensor if readings become unreliable

### Cleaning

1. Power off Raspberry Pi
2. Use soft, dry cloth to wipe sensor lens
3. Avoid liquids (not waterproof)
4. Don't touch sensor lens directly

---

## Safety Warnings

⚠️ **CRITICAL SAFETY INFORMATION:**

1. **Voltage Supply**
   - Never supply more than 3.3V to GPIO pins directly
   - 5V sensor modules must regulate to 3.3V before GPIO

2. **Current Limits**
   - GPIO pins can source/sink maximum 16mA per pin
   - Total per bank: 50mA
   - LEDs at 20mA = 1.5V drop + resistor required

3. **Power Supply**
   - Use quality PSU with at least 2A capacity
   - Protect against power surges with UPS if critical

4. **Electrical Hazards**
   - Unplug before modifying wiring
   - Never touch exposed circuit traces during operation
   - Wear ESD wrist strap when handling sensitive components

---

**For questions, refer to INSTALLATION.md or check the Raspberry Pi GPIO documentation.**

Last Updated: 2024
Tested on Raspberry Pi 4B with Raspberry Pi OS Bookworm
