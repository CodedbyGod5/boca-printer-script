# Boca Printer Paper Monitor - Installation & Setup Guide

## System Overview

This system provides a **Telnet-based paper monitoring service** for a Boca printer on Raspberry Pi.

**Architecture:**
- **Raspberry Pi**: Runs Telnet server (listening for status queries)
- **Inner Mapper**: Client that polls Pi every 60 seconds via Telnet
- **Reflective Light Sensor**: Detects when paper runs out
- **LED Indicators** (optional): Visual status indicators (Green=OK, Red=Out)

---

## Prerequisites

### Hardware Required
1. **Raspberry Pi** (4B recommended, 3B+ minimum)
   - Raspberry Pi OS Bookworm (or newer)
   - 1 GB RAM minimum (2GB recommended)
   - Stable power supply

2. **Reflective Light Sensor**
   - IR or visible light reflective sensor (e.g., E18-D80NK, QTR-8RC)
   - 3.3V compatible input
   - Pull-up/pull-down resistor configuration

3. **Optional Components**
   - Red LED + 330Ω resistor (paper out indicator)
   - Green LED + 330Ω resistor (paper OK indicator)
   - Jumper wires and breadboard

4. **Boca Printer**
   - Must have a reflective backing plate under the paper stack
   - This creates the detection surfaceZ

### Software Requirements
- Raspberry Pi OS Bookworm (or Ubuntu Server 22.04 LTS for Pi)
- Python 3.9 or newer
- pip3 package manager
- systemd (for service management)

---

## Installation Steps

### Step 1: Prepare Raspberry Pi

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python and essential tools
sudo apt install -y python3 python3-pip python3-dev git

# Install pigpio daemon (for reliable GPIO control)
sudo apt install -y pigpio python3-gpiozero

# Start pigpio service
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

### Step 2: Create Installation Directory

```bash
# Create installation directory
sudo mkdir -p /opt/printer_monitor
sudo chown pi:pi /opt/printer_monitor

# Create log directory
sudo mkdir -p /var/log
sudo touch /var/log/printer_monitor.log
sudo chown pi:pi /var/log/printer_monitor.log
```

### Step 3: Copy Files to Raspberry Pi

**Option A: Using SCP (from your development machine)**
```bash
# Copy main script
scp printer_monitor.py pi@raspberrypi.local:/opt/printer_monitor/

# Copy requirements
scp requirements.txt pi@raspberrypi.local:/opt/printer_monitor/

# Copy systemd service file
scp printer_monitor.service pi@raspberrypi.local:/tmp/
```

**Option B: Using Git**
```bash
cd /opt/printer_monitor
git clone <your-repo-url> .
```

### Step 4: Install Python Dependencies

```bash
cd /opt/printer_monitor

# Install required packages
sudo pip3 install -r requirements.txt

# Verify installation
python3 -c "import gpiozero; print('gpiozero OK')"
python3 -c "import socket; print('socket OK')"
```

### Step 5: Make Script Executable

```bash
chmod +x /opt/printer_monitor/printer_monitor.py
```

### Step 6: Test in Debug Mode (Optional)

```bash
# Test with simulated hardware (no GPIO required)
cd /opt/printer_monitor

# Edit printer_monitor.py to set DEBUG_MODE = True

# Run test
python3 printer_monitor.py

# Expected output:
# Printer Monitor Starting
# Sensor running in SIMULATION mode
# Telnet server started on 0.0.0.0:2323
```

### Step 7: Test Sensor Connection

```bash
# Before installing as service, test with GPIO
python3 printer_monitor.py &

# In another terminal, test Telnet
telnet localhost 2323
# Type: STATUS
# Expected: PAPER_OK or OUT_OF_PAPER

# Stop the process
pkill -f printer_monitor.py
```

### Step 8: Install as systemd Service

```bash
# Copy service file to systemd directory
sudo cp printer_monitor.service /etc/systemd/system/

# Set proper permissions
sudo chmod 644 /etc/systemd/system/printer_monitor.service

# Enable service (runs on boot)
sudo systemctl enable printer_monitor

# Start service immediately
sudo systemctl start printer_monitor

# Check status
sudo systemctl status printer_monitor

# View logs
sudo journalctl -u printer_monitor -f
```

---

## Configuration

### Edit Configuration Variables

Open `/opt/printer_monitor/printer_monitor.py` and modify these top-level variables:

```python
# GPIO Pin Configuration
SENSOR_PIN = 17                    # Change to your sensor pin
GREEN_LED_PIN = 27                 # Change to your green LED pin
RED_LED_PIN = 22                   # Change to your red LED pin
USE_LEDS = True                    # Set to False if no LEDs

# Sensor Configuration
DEBOUNCE_COUNT = 5                 # Readings required before state change
SENSOR_READ_INTERVAL = 0.5         # Seconds between sensor reads

# Telnet Server Configuration
TELNET_PORT = 23                   # Or use 2323 if no root privileges
LISTEN_ADDRESS = "0.0.0.0"         # Accessible from network

# Logging
LOG_FILE_PATH = "/var/log/printer_monitor.log"
LOG_LEVEL = logging.INFO

# Feature Flags
DEBUG_MODE = False                 # Set to True to test without hardware
SIMULATE_PAPER_OUT = False         # For testing paper-out state
ENABLE_HEARTBEAT_LOGGING = True    # Periodic status logging
```

### Configuration for Non-Root Telnet (Port > 1024)

If the service cannot bind to port 23 (requires root), modify:

```bash
# Option 1: Use alternative port (2323)
TELNET_PORT = 2323

# Option 2: Grant CAP_NET_BIND_SERVICE capability
sudo setcap 'cap_net_bind_service=+ep' /usr/bin/python3
```

### Enable Alternative Port in Inner Mapper

Update Inner Mapper configuration to connect to port 2323 (or your chosen port).

---

## System Service Management

### Basic Commands

```bash
# Start service
sudo systemctl start printer_monitor

# Stop service
sudo systemctl stop printer_monitor

# Restart service
sudo systemctl restart printer_monitor

# Check status
sudo systemctl status printer_monitor

# View recent logs
sudo journalctl -u printer_monitor -n 50

# Follow live logs
sudo journalctl -u printer_monitor -f

# Disable auto-start on boot
sudo systemctl disable printer_monitor

# Re-enable auto-start on boot
sudo systemctl enable printer_monitor
```

### Monitoring Service Health

```bash
# Check if service is active
systemctl is-active printer_monitor

# Check if service is enabled on boot
systemctl is-enabled printer_monitor

# View detailed service info
systemctl show printer_monitor

# Check restart count
systemctl show printer_monitor -p NRestarts
```

### Troubleshooting Service Issues

```bash
# Check systemd error logs
sudo journalctl -u printer_monitor -p err

# Check service file syntax
sudo systemd-analyze verify /etc/systemd/system/printer_monitor.service

# Reload systemd configuration after changes
sudo systemctl daemon-reload
sudo systemctl restart printer_monitor
```

---

## Telnet Protocol Reference

### Connection

```
telnet <raspberry-pi-ip> 23
# or
telnet <raspberry-pi-ip> 2323
```

### Request Format

```
STATUS
```

### Response Formats

```
PAPER_OK           - Paper is present in printer
OUT_OF_PAPER       - Paper has run out
SENSOR_ERROR       - Sensor is disconnected or malfunctioning
INITIALIZING       - System is still starting up
UNKNOWN_COMMAND    - Invalid command received
```

### Example Session

```bash
$ telnet 192.168.1.100 23
Trying 192.168.1.100...
Connected to 192.168.1.100.
Escape character is '^]'.
STATUS
PAPER_OK
Connection closed by foreign host.
```

---

## Testing and Troubleshooting

### Test Without Hardware (Debug Mode)

```bash
# Edit printer_monitor.py
DEBUG_MODE = True
SIMULATE_PAPER_OUT = False  # For PAPER_OK response
# or
SIMULATE_PAPER_OUT = True   # For OUT_OF_PAPER response

# Run directly
python3 /opt/printer_monitor/printer_monitor.py

# In another terminal, test
telnet localhost 2323
```

### Manual Telnet Test from Command Line

```bash
# Test connection
timeout 2 telnet 192.168.1.100 23 << EOF
STATUS
quit
EOF

# Using netcat (alternative)
echo "STATUS" | nc 192.168.1.100 23

# Using socat (another alternative)
echo "STATUS" | socat - TCP:192.168.1.100:23
```

### Check GPIO Pin Status

```bash
# List all GPIO pins
gpio readall

# Read specific pin status
gpio read 17

# Set GPIO mode
gpio mode 17 in
```

### Monitor Real-Time Logs

```bash
# Follow service logs live
sudo journalctl -u printer_monitor -f

# Follow with grepping for specific issues
sudo journalctl -u printer_monitor -f | grep -i error

# View last 100 lines
sudo journalctl -u printer_monitor -n 100
```

### Check Network Connectivity

```bash
# Test if Telnet service is listening
sudo netstat -tlnp | grep python3

# Alternative using ss
sudo ss -tlnp | grep python3

# Test from another machine
telnet <pi-ip> 23
```

### Verify Pigpio is Running

```bash
# Check if pigpiod daemon is active
sudo systemctl status pigpiod

# Test pigpio connection
python3 -c "from gpiozero.pins.pigpio import PiGPIOFactory; f = PiGPIOFactory(); print('OK')"
```

---

## Log File Location and Analysis

### Default Log Path
```
/var/log/printer_monitor.log
```

### View Logs

```bash
# Real-time monitoring
tail -f /var/log/printer_monitor.log

# Last 50 lines
tail -50 /var/log/printer_monitor.log

# Search for errors
grep ERROR /var/log/printer_monitor.log

# Search for status changes
grep "Status changed" /var/log/printer_monitor.log

# Filter by date/time
grep "2024-01-15" /var/log/printer_monitor.log
```

### Log Rotation

Logs are managed by systemd journaling. For file-based logs:

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/printer_monitor

# Add:
# /var/log/printer_monitor.log {
#     daily
#     rotate 5
#     compress
#     delaycompress
#     missingok
#     notifempty
#     create 0640 pi pi
#     sharedscripts
#     postrotate
#         systemctl reload printer_monitor > /dev/null 2>&1 || true
#     endscript
# }
```

---

## Performance Optimization

### CPU Usage

The system is optimized for minimal CPU usage:
- **Sensor read interval**: 0.5 seconds (adjustable)
- **Debounce count**: 5 reads minimum (prevents false positives)
- **Thread pool**: Limited to 5 concurrent clients
- **Memory limit**: 256MB (systemd service)
- **CPU quota**: 50% (systemd service)

### Memory Usage

Typical memory footprint:
- Base Python: ~25-30 MB
- gpiozero library: ~5-10 MB
- Total: ~40-50 MB at rest

### Network Optimization

- Telnet protocol is lightweight (text-based)
- Connection timeout: 10 seconds (prevents hanging clients)
- No persistent connections required
- Inner Mapper can poll safely at 60-second intervals

---

## GPIO Pin Reference Table

| Component | Function | GPIO Pin | Circuit |
|-----------|----------|----------|---------|
| Light Sensor | Input | GPIO 17 | 3.3V → Sensor → GPIO17 (with pull-up) |
| Green LED | Output | GPIO 27 | GPIO27 → 330Ω resistor → LED → GND |
| Red LED | Output | GPIO 22 | GPIO22 → 330Ω resistor → LED → GND |

---

## Common Issues and Solutions

### Issue: Cannot Bind to Port 23

**Symptom:** `Permission denied` when starting service

**Solutions:**
1. Use alternative port 2323 (recommended)
2. Run as root (not recommended)
3. Grant capability: `sudo setcap 'cap_net_bind_service=+ep' /usr/bin/python3`

### Issue: gpiozero Not Found

**Symptom:** `ModuleNotFoundError: No module named 'gpiozero'`

**Solutions:**
```bash
sudo pip3 install --upgrade gpiozero
sudo pip3 install pigpio
```

### Issue: Sensor Always Returns Same Value

**Symptom:** Never changes from PAPER_OK or OUT_OF_PAPER

**Solutions:**
1. Check GPIO pin number matches configuration
2. Test sensor with simple GPIO read script
3. Increase DEBOUNCE_COUNT to allow more readings
4. Check sensor wiring and power supply

### Issue: Telnet Connection Refused

**Symptom:** `Connection refused` when testing

**Solutions:**
1. Check service is running: `sudo systemctl status printer_monitor`
2. Check port number: verify TELNET_PORT in config
3. Check firewall: `sudo ufw allow 23/tcp` or `sudo ufw allow 2323/tcp`
4. Check IP address: use `hostname -I` to get Pi's IP

### Issue: High CPU Usage

**Symptom:** CPU constantly at 100%

**Solutions:**
1. Increase SENSOR_READ_INTERVAL (default 0.5s)
2. Check for error loops in logs
3. Restart service: `sudo systemctl restart printer_monitor`
4. Disable DEBUG_MODE if enabled

---

## Inner Mapper Integration

See the separate **INNER_MAPPER_INTEGRATION.md** for detailed instructions on configuring Inner Mapper to poll this Telnet server.

---

## Security Considerations

### Network Security

1. **Firewall Rules**
   ```bash
   # Allow Telnet only from specific IP (Inner Mapper)
   sudo ufw allow from 192.168.1.50 to any port 23
   
   # Or allow entire local network
   sudo ufw allow from 192.168.1.0/24 to any port 23
   ```

2. **User Permissions**
   - Service runs as `pi` user (non-root)
   - Log file readable by log aggregation tools
   - GPIO access via `pigpiod` daemon

3. **No Authentication**
   - Telnet protocol has no built-in authentication
   - Rely on firewall rules to restrict access
   - Consider VPN if accessed over untrusted networks

### Data Security

1. **Log File Permissions**
   ```bash
   sudo chmod 640 /var/log/printer_monitor.log
   sudo chown pi:pi /var/log/printer_monitor.log
   ```

2. **Configuration Security**
   ```bash
   sudo chmod 640 /opt/printer_monitor/printer_monitor.py
   ```

### Hardware Security

1. **GPIO Access**
   - Service uses pigpio daemon (more secure than direct GPIO)
   - Only one user can access GPIO at a time

2. **Sensor Protection**
   - Mount sensor in weatherproof enclosure
   - Protect cables from physical damage
   - Use shielded wires for long runs

---

## Future Enhancements

### Planned Features

1. **REST API Endpoint**
   - JSON status responses
   - Compatible with modern monitoring systems
   - Webhook support for alerts

2. **MQTT Integration**
   - Publish status to MQTT broker
   - Compatible with Home Assistant, OpenHAB

3. **Multi-Printer Support**
   - Single Pi monitoring multiple printers
   - Separate sensors on different GPIO pins

4. **Docker Containerization**
   - Easy deployment on any system
   - CI/CD pipeline ready

5. **Web Dashboard**
   - Real-time status display
   - Historical data visualization
   - Alert configuration UI

---

## Getting Help

### Debug Commands

```bash
# Full system diagnostic
python3 /opt/printer_monitor/printer_monitor.py --debug

# Test sensor only
python3 -c "from printer_monitor import SensorManager; s = SensorManager(17, 5, None)"

# Check Python version
python3 --version

# Check pip packages
pip3 list | grep -i gpio

# System information
uname -a
cat /etc/os-release
```

### Support Resources

- Raspberry Pi Forum: https://www.raspberrypi.org/forums/
- gpiozero Documentation: https://gpiozero.readthedocs.io/
- Python Telnet: https://docs.python.org/3/library/telnetlib.html

---

## License and Attribution

This monitoring system is provided as-is for the Boca printer integration project.

---

**Last Updated:** 2024
**Tested On:** Raspberry Pi 4B, Raspberry Pi OS Bookworm
**Python Version:** 3.9+
