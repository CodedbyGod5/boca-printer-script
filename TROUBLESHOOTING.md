# Boca Printer Paper Monitor - Troubleshooting Guide

## Quick Reference

| Symptom | Probable Cause | Solution |
|---------|---|---|
| Service won't start | gpiozero not installed | `sudo pip3 install gpiozero pigpio` |
| Always returns "PAPER_OK" | Sensor not reading reflection | Check GPIO pin number, verify sensor power |
| Always returns "OUT_OF_PAPER" | Sensor inverted logic | Verify reflection detection setup |
| Telnet "Connection refused" | Port 23 permission denied | Use port 2323 or grant CAP_NET_BIND_SERVICE |
| Telnet timeout | Service not listening | Check `systemctl status printer_monitor` |
| High CPU usage | Tight read loop | Increase SENSOR_READ_INTERVAL |
| LED not lighting | Wrong polarity or no power | Check long leg = GPIO side, verify 330Ω resistor |

---

## Error Messages and Solutions

### "ModuleNotFoundError: No module named 'gpiozero'"

**Cause:** gpiozero library not installed

**Solutions:**
```bash
# Install missing library
sudo pip3 install gpiozero

# Or install all requirements
cd /opt/printer_monitor
sudo pip3 install -r requirements.txt

# Verify installation
python3 -c "import gpiozero; print('OK')"
```

---

### "PermissionError: Cannot bind to port 23"

**Cause:** Port 23 requires root privileges, service runs as 'pi' user

**Solutions:**

**Option 1: Use alternative port (RECOMMENDED)**
```bash
# Edit printer_monitor.py
TELNET_PORT = 2323

# Restart service
sudo systemctl restart printer_monitor

# Update Inner Mapper to connect to port 2323
```

**Option 2: Grant capability to Python**
```bash
# Give Python permission to bind to privileged ports
sudo setcap 'cap_net_bind_service=+ep' /usr/bin/python3

# Restart service
sudo systemctl restart printer_monitor

# Verify
sudo getcap /usr/bin/python3
```

**Option 3: Run as root (NOT RECOMMENDED for security)**
```bash
# Edit /etc/systemd/system/printer_monitor.service
User=root

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart printer_monitor
```

---

### "RuntimeError: No edge detection implementation available"

**Cause:** GPIO library not properly initialized, pigpio daemon not running

**Solutions:**
```bash
# Check if pigpio daemon is running
sudo systemctl status pigpiod

# Start pigpio if not running
sudo systemctl start pigpiod

# Enable auto-start on boot
sudo systemctl enable pigpiod

# Verify pigpio responds
pigs hwver

# If pigpio won't start, check permissions
sudo usermod -a -G gpio pi

# Logout and login for group changes to take effect
exit
```

---

### "ConnectionRefusedError: [Errno 111] Connection refused"

**Cause:** Telnet server not listening or wrong port/IP

**Solutions:**
```bash
# Check service status
sudo systemctl status printer_monitor

# Check if service is actually running
ps aux | grep printer_monitor

# Verify port is open
sudo netstat -tlnp | grep python3

# Try alternative port
telnet localhost 2323

# Check if service crashed
sudo journalctl -u printer_monitor -n 20

# Restart service
sudo systemctl restart printer_monitor
```

---

### "Sensor timeout: no read for X seconds"

**Cause:** GPIO pin not reading, sensor disconnected

**Solutions:**
```bash
# Test sensor pin directly
gpio -g read 17

# Check GPIO mode
gpio -g mode 17 in

# Verify sensor power
# Use multimeter: sensor VCC pin should show ~5V

# Check for loose connections
# Reseat all jumper wires

# Test with different GPIO pin
# Edit printer_monitor.py: SENSOR_PIN = 27 (try different pin)
```

---

### "DEBUG: Sensor running in SIMULATION mode"

**Cause:** DEBUG_MODE is set to True

**Solutions:**
```bash
# This is intentional for testing without hardware
# Disable debug mode for production:

# Edit printer_monitor.py
DEBUG_MODE = False

# Restart service
sudo systemctl restart printer_monitor

# Verify it's using hardware
sudo journalctl -u printer_monitor -f | grep -i sensor
```

---

## Diagnostic Procedures

### 1. Service Health Check

```bash
#!/bin/bash
echo "=== Printer Monitor Health Check ==="

# Check service status
echo "Service Status:"
sudo systemctl status printer_monitor --no-pager

# Check resource usage
echo -e "\nResource Usage:"
ps aux | grep printer_monitor | grep -v grep

# Check recent logs
echo -e "\nRecent Errors (last 10):"
sudo journalctl -u printer_monitor -p err -n 10 --no-pager

# Check network listening
echo -e "\nNetwork Listening:"
sudo netstat -tlnp 2>/dev/null | grep -i python

# Uptime
echo -e "\nService Uptime:"
systemctl show printer_monitor --property=ActiveEnterTimestamp
```

### 2. GPIO and Hardware Test

```bash
#!/bin/bash
echo "=== GPIO Hardware Test ==="

# List all GPIO pins
echo "GPIO Pin Status:"
gpio readall

# Test sensor pin (GPIO 17)
echo -e "\nTesting Sensor Pin (GPIO 17):"
gpio -g mode 17 in
for i in {1..5}; do
    echo -n "Read $i: "
    gpio -g read 17
    sleep 0.5
done

# Test green LED pin (GPIO 27)
echo -e "\nTesting Green LED (GPIO 27):"
gpio -g mode 27 out
gpio -g write 27 1
echo "LED ON (should see green light)"
sleep 1
gpio -g write 27 0
echo "LED OFF"

# Test red LED pin (GPIO 22)
echo -e "\nTesting Red LED (GPIO 22):"
gpio -g mode 22 out
gpio -g write 22 1
echo "LED ON (should see red light)"
sleep 1
gpio -g write 22 0
echo "LED OFF"
```

### 3. Network and Telnet Test

```bash
#!/bin/bash
echo "=== Network Connectivity Test ==="

# Check localhost
echo "Test localhost Telnet:"
echo "STATUS" | timeout 2 nc localhost 2323 && echo "✓ Success" || echo "✗ Failed"

# Check specific port
echo -e "\nChecking port 2323:"
sudo ss -tlnp | grep :2323

# Test from current system
echo -e "\nLocal network test (replace with actual Pi IP):"
PI_IP="192.168.1.100"
echo "STATUS" | timeout 2 nc $PI_IP 2323 && echo "✓ Success" || echo "✗ Failed"

# Detailed telnet test
echo -e "\nDetailed Telnet connection:"
timeout 5 telnet localhost 2323 << EOF
STATUS
EOF
```

### 4. Log Analysis

```bash
# Real-time monitoring
sudo journalctl -u printer_monitor -f

# Last 50 lines
sudo journalctl -u printer_monitor -n 50 --no-pager

# Just errors
sudo journalctl -u printer_monitor -p err --no-pager

# Date-based filtering
sudo journalctl -u printer_monitor --since "2024-01-15 08:00:00" --until "2024-01-15 09:00:00"

# Count specific messages
sudo journalctl -u printer_monitor | grep -c "Status changed"

# Find all status changes
sudo journalctl -u printer_monitor | grep "Status changed"

# Export logs to file
sudo journalctl -u printer_monitor -n 1000 > /tmp/printer_monitor.log
cat /tmp/printer_monitor.log
```

---

## Common Scenarios and Fixes

### Scenario 1: Service Starts but Always Says "PAPER_OK"

**Diagnostics:**
```bash
# 1. Verify sensor is reading
gpio -g read 17
# Should alternate between 0 (paper) and 1 (no paper) when you wave your hand

# 2. Check sensor power
# Multimeter on sensor VCC pin should show ~5V

# 3. Verify GPIO pin number
grep "SENSOR_PIN" /opt/printer_monitor/printer_monitor.py

# 4. Test raw sensor reading
python3 << 'EOF'
from gpiozero import DigitalInputDevice
sensor = DigitalInputDevice(17)
for i in range(10):
    print(f"Read {i}: {sensor.value}")
    import time; time.sleep(0.1)
EOF
```

**Fix:**
```bash
# If sensor reads correctly but status never changes:
# 1. Increase DEBOUNCE_COUNT to verify reads are stable
# 2. Check if sensor is inverted in logic:
#    - HIGH (1) should mean "paper out" (reflection detected)
#    - LOW (0) should mean "paper present" (no reflection)

# If logic is inverted, modify printer_monitor.py line ~300:
# Change: if reading:  to  if not reading:
```

---

### Scenario 2: Service Crashes Repeatedly

**Diagnostics:**
```bash
# 1. Check restart count
systemctl show printer_monitor -p NRestarts

# 2. Read last error
sudo journalctl -u printer_monitor -p err -n 1

# 3. Run service in foreground to see full error
sudo -u pi python3 /opt/printer_monitor/printer_monitor.py
```

**Common Crash Causes:**

**A. pigpio daemon not running**
```bash
sudo systemctl start pigpiod
sudo systemctl enable pigpiod
```

**B. GPIO already in use**
```bash
# Check what's using GPIO
ps aux | grep gpio
# Kill conflicting processes
sudo pkill -f gpio_program
```

**C. Permission issues**
```bash
# Verify file permissions
ls -la /opt/printer_monitor/printer_monitor.py
# Should be readable by 'pi' user

# Fix permissions
sudo chown pi:pi /opt/printer_monitor/printer_monitor.py
sudo chmod 755 /opt/printer_monitor/printer_monitor.py
```

---

### Scenario 3: High CPU Usage (100% constant)

**Diagnostics:**
```bash
# 1. Check CPU usage
top -b -n 1 | grep printer_monitor

# 2. Look for error loops
sudo journalctl -u printer_monitor -f | head -20
```

**Causes and Fixes:**

```python
# A. Too-fast read interval
# In printer_monitor.py, INCREASE this value:
SENSOR_READ_INTERVAL = 0.5  # Change to 1.0 or 2.0

# B. Infinite error loop
# Look for repeating errors in logs
# Fix underlying GPIO/sensor issue

# C. Thread explosion
# Check for connection leak
sudo netstat -tulnp | grep python3
# Should show only 1 or 2 connections, not hundreds
```

---

### Scenario 4: Telnet Connection Timeout

**Diagnostics:**
```bash
# 1. Verify service is listening
sudo ss -tlnp | grep :2323

# 2. Check firewall
sudo ufw status
sudo ufw allow 2323

# 3. Test connectivity
telnet localhost 2323

# 4. Check if port changed
grep TELNET_PORT /opt/printer_monitor/printer_monitor.py
```

**Fixes:**
```bash
# A. Firewall blocking
sudo ufw allow 2323/tcp

# B. Service not listening
sudo systemctl restart printer_monitor
sudo systemctl status printer_monitor

# C. Port in use by something else
sudo netstat -tulnp | grep 2323
# If another process using it, stop that process
```

---

### Scenario 5: LEDs Not Responding to Status Changes

**Diagnostics:**
```bash
# 1. Verify USE_LEDS is True in config
grep "USE_LEDS" /opt/printer_monitor/printer_monitor.py

# 2. Test LED pins manually
# Green LED (GPIO 27)
gpio -g mode 27 out
gpio -g write 27 1  # Should light up
gpio -g write 27 0  # Should turn off

# Red LED (GPIO 22)
gpio -g mode 22 out
gpio -g write 22 1  # Should light up
gpio -g write 22 0  # Should turn off

# 3. Check wiring
# Use multimeter to verify:
# - Voltage at GPIO pin: 3.3V when ON, 0V when OFF
# - LED polarity: long leg on GPIO side, short leg to GND
# - Resistor value: Should measure ~330Ω
```

**Fixes:**
```bash
# A. Wrong GPIO pin
grep -E "RED_LED_PIN|GREEN_LED_PIN" /opt/printer_monitor/printer_monitor.py
# Verify pin numbers match your wiring

# B. LED polarity reversed
# Long leg must connect to resistor/GPIO side
# Short leg must connect to GND

# C. Missing resistor
# LEDs require 330Ω resistor in series
# Without it, LED may work but GPIO can be damaged

# D. LED failed
# Replace LED with known working LED
```

---

## Reset and Recovery

### Full System Reset

```bash
#!/bin/bash
# WARNING: This resets all configuration. Use only if necessary.

echo "Resetting Printer Monitor..."

# 1. Stop service
sudo systemctl stop printer_monitor

# 2. Clear any stuck GPIO
python3 << 'EOF'
try:
    from gpiozero import LED
    led1 = LED(27)
    led2 = LED(22)
    led1.off()
    led2.off()
    led1.close()
    led2.close()
    print("GPIO reset OK")
except: pass
EOF

# 3. Clean up Python cache
rm -rf /opt/printer_monitor/__pycache__
find /opt/printer_monitor -name "*.pyc" -delete

# 4. Restart pigpio
sudo systemctl restart pigpiod

# 5. Restart service
sudo systemctl start printer_monitor

# 6. Verify
sudo systemctl status printer_monitor
```

### Reinstall from Scratch

```bash
#!/bin/bash
# Complete clean reinstall

echo "Full Reinstall..."

# 1. Stop service
sudo systemctl stop printer_monitor

# 2. Remove old files
sudo rm -rf /opt/printer_monitor
sudo rm -f /etc/systemd/system/printer_monitor.service

# 3. Clean Python packages (optional)
sudo pip3 uninstall -y gpiozero pigpio

# 4. Reinstall clean
sudo mkdir -p /opt/printer_monitor
sudo chown pi:pi /opt/printer_monitor

# 5. Copy fresh files
cp printer_monitor.py /opt/printer_monitor/
cp requirements.txt /opt/printer_monitor/
cp printer_monitor.service /tmp/

# 6. Install dependencies
cd /opt/printer_monitor
sudo pip3 install -r requirements.txt

# 7. Install service
sudo cp /tmp/printer_monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable printer_monitor
sudo systemctl start printer_monitor

# 8. Verify
sleep 2
sudo systemctl status printer_monitor
```

---

## Performance Tuning

### Optimize for Speed

```python
# In printer_monitor.py, for faster response time:

DEBOUNCE_COUNT = 3                  # Lower from 5
SENSOR_READ_INTERVAL = 0.1          # Lower from 0.5
HEARTBEAT_INTERVAL = 300            # Increase from 60
ENABLE_HEARTBEAT_LOGGING = False    # Disable if not needed
```

**Trade-off:** Faster response but more false positives

### Optimize for Stability

```python
# For very noisy environments:

DEBOUNCE_COUNT = 10                 # Higher from 5
SENSOR_READ_INTERVAL = 1.0          # Higher from 0.5
SENSOR_TIMEOUT = 20                 # Increase from 10
HEARTBEAT_INTERVAL = 120            # Increase from 60
```

**Trade-off:** More stable but slower to detect state changes

### Optimize for Low Power

```python
# For battery-powered Pi or UPS systems:

SENSOR_READ_INTERVAL = 5.0          # Much higher
HEARTBEAT_INTERVAL = 600            # Much higher (10 minutes)
ENABLE_HEARTBEAT_LOGGING = False    # Disable logging overhead
USE_LEDS = False                    # Disable LED power draw
DEBUG_MODE = False                  # Ensure not in debug
```

---

## Monitoring and Alerting

### Create Alert Rules

```bash
# Monitor for recurring errors
sudo journalctl -u printer_monitor | tail -100 | grep -c "error"

# Alert if service is down
#!/bin/bash
if ! systemctl is-active --quiet printer_monitor; then
    echo "ALERT: Printer monitor service is down"
    # Send email, webhook, etc.
fi

# Check for frequent status changes (possible sensor flapping)
sudo journalctl -u printer_monitor | grep "Status changed" | wc -l
# If > 20 changes in 1 hour, sensor may be flapping
```

### Create Watchdog

```bash
#!/bin/bash
# Check service health every minute and restart if needed

while true; do
    if ! systemctl is-active --quiet printer_monitor; then
        echo "Service down, restarting..."
        sudo systemctl restart printer_monitor
    fi
    
    # Check for communication errors
    recent_errors=$(sudo journalctl -u printer_monitor -u printer_monitor --since="1 minute ago" | grep -c "error")
    if [ "$recent_errors" -gt 5 ]; then
        echo "Too many errors, restarting..."
        sudo systemctl restart printer_monitor
    fi
    
    sleep 60
done
```

---

## Getting Help

### Collect Diagnostic Information

```bash
#!/bin/bash
# Collect all diagnostic info for support

OUTPUT_DIR="/tmp/printer_monitor_diagnostics_$(date +%s)"
mkdir -p $OUTPUT_DIR

echo "Collecting diagnostics to $OUTPUT_DIR..."

# System info
echo "=== System Information ===" > $OUTPUT_DIR/01_system_info.txt
uname -a >> $OUTPUT_DIR/01_system_info.txt
cat /etc/os-release >> $OUTPUT_DIR/01_system_info.txt
df -h >> $OUTPUT_DIR/01_system_info.txt

# Service status
echo "=== Service Status ===" > $OUTPUT_DIR/02_service_status.txt
sudo systemctl status printer_monitor --no-pager >> $OUTPUT_DIR/02_service_status.txt
ps aux | grep printer_monitor >> $OUTPUT_DIR/02_service_status.txt

# Network info
echo "=== Network Configuration ===" > $OUTPUT_DIR/03_network.txt
sudo netstat -tlnp >> $OUTPUT_DIR/03_network.txt
hostname -I >> $OUTPUT_DIR/03_network.txt

# GPIO info
echo "=== GPIO Status ===" > $OUTPUT_DIR/04_gpio.txt
gpio readall >> $OUTPUT_DIR/04_gpio.txt 2>&1

# Latest logs (last 1000 lines)
sudo journalctl -u printer_monitor -n 1000 > $OUTPUT_DIR/05_service_logs.txt

# Config
cp /opt/printer_monitor/printer_monitor.py $OUTPUT_DIR/06_config.py

# Package versions
pip3 list | grep -E "gpiozero|pigpio" > $OUTPUT_DIR/07_packages.txt

echo "Diagnostics collected to: $OUTPUT_DIR"
echo "Please share this directory with support team"
tar -czf /tmp/printer_monitor_diagnostics_$(date +%s).tar.gz $OUTPUT_DIR
```

---

## Contact Support

If troubleshooting doesn't resolve the issue:

1. **Collect diagnostic information** (see above)
2. **Describe the problem:**
   - What is the symptom?
   - When did it start?
   - What has changed recently?
   - Have you modified any configuration?

3. **Provide logs:**
   - Last 100 lines of service logs
   - Hardware configuration
   - Network setup diagram

4. **Available Channels:**
   - Raspberry Pi Forum
   - GitHub Issues (if open-source repo)
   - Internal support team

---

**Last Updated:** 2024
**Document Version:** 1.0
