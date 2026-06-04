# Printer Paper Monitor - Simple Version

A simple telnet server that monitors printer paper status using a GPIO sensor.

## What It Does

- Monitors a reflective light sensor on GPIO pin 17
- Runs a telnet server on port 2323
- Responds with `PAPER_OK` or `OUT_OF_PAPER` status

## Hardware Setup

1. **Raspberry Pi** (any model)
2. **Reflective light sensor** (e.g., E18-D80NK, QTR-8RC)
   - Connected to GPIO 17 (pin 11)
   - 3.3V compatible
3. **Jumper wires** to connect sensor to Pi

## Installation

### 1. Install Python (Raspberry Pi OS comes with Python 3)

```bash
sudo apt update
sudo apt install python3-pip python3-gpiozero
```

### 2. Download and Setup

```bash
cd /path/to/printer/script
pip3 install -r requirements.txt
chmod +x monitor.py
```

### 3. Run the Script

```bash
python3 monitor.py
```

You should see:
```
Sensor initialized on GPIO 17
Telnet server listening on port 2323
```

## Testing

From another terminal or device:

```bash
telnet localhost 2323
```

At the telnet prompt, type:
```
STATUS
```

Response will be:
- `PAPER_OK` - Paper present
- `OUT_OF_PAPER` - Paper out
- `SENSOR_ERROR` - Sensor error

Type `QUIT` to exit.

## Auto-Start (Optional)

To run on boot, create a systemd service:

```bash
sudo nano /etc/systemd/system/printer-monitor.service
```

Paste this:

```ini
[Unit]
Description=Printer Paper Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/path/to/printer/script
ExecStart=/usr/bin/python3 /path/to/printer/script/monitor.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable printer-monitor.service
sudo systemctl start printer-monitor.service
```

## Configuration

Edit the top of `monitor.py` to change:
- `SENSOR_PIN` - GPIO pin number (default: 17)
- `TELNET_PORT` - Port to listen on (default: 2323)
- `DEBOUNCE_READS` - Readings before state change (default: 5)

## Troubleshooting

**"gpiozero not installed"**: Install with `sudo apt install python3-gpiozero`

**Sensor not responding**: Check GPIO pin connections and try simulation mode by removing gpiozero

**Permission denied on GPIO**: Run with `sudo python3 monitor.py`

## Files

- `monitor.py` - Main script (only file needed!)
- `requirements.txt` - Dependencies
- `printer-monitor.service` - Systemd service (optional)

│                    └──────────────┘                         │
│                                                              │
│  GPIO Pins:                                                 │
│  - GPIO 17: Reflective Light Sensor Input                  │
│  - GPIO 27: Green LED (Paper OK) - Optional                │
│  - GPIO 22: Red LED (Paper Out) - Optional                 │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ GPIO
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     HARDWARE                                │
│  ┌──────────────────┐                                       │
│  │ Reflective Light │ ← Detects when paper runs out        │
│  │     Sensor       │   (reflects off backing plate)        │
│  └──────────────────┘                                       │
│  ┌──────────────────┐ ┌──────────────────┐                 │
│  │  Green LED       │ │  Red LED         │                 │
│  │  (Optional)      │ │  (Optional)      │                 │
│  └──────────────────┘ └──────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Raspberry Pi 4B or 3B+ with Raspberry Pi OS Bookworm
- Reflective light sensor connected to GPIO 17
- Network connectivity
- SSH access to Pi

### Installation

```bash
# 1. SSH into Raspberry Pi
ssh pi@raspberrypi.local

# 2. Update system
sudo apt update && sudo apt upgrade -y

# 3. Install dependencies
sudo apt install -y python3 python3-pip python3-dev pigpio python3-gpiozero

# 4. Create installation directory
sudo mkdir -p /opt/printer_monitor
sudo chown pi:pi /opt/printer_monitor
cd /opt/printer_monitor

# 5. Copy files (from your development machine using scp)
# scp printer_monitor.py pi@raspberrypi.local:/opt/printer_monitor/
# scp requirements.txt pi@raspberrypi.local:/opt/printer_monitor/
# scp printer_monitor.service pi@raspberrypi.local:/tmp/

# 6. Install Python packages
pip3 install -r requirements.txt

# 7. Install systemd service
sudo cp printer_monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable printer_monitor
sudo systemctl start printer_monitor

# 8. Verify status
sudo systemctl status printer_monitor

# 9. Test Telnet connection
telnet localhost 2323
# Type: STATUS
# Expected: PAPER_OK or OUT_OF_PAPER
```

### Next Steps
- See [INSTALLATION.md](INSTALLATION.md) for detailed setup
- See [WIRING_GUIDE.md](WIRING_GUIDE.md) for hardware wiring
- See [INNER_MAPPER_INTEGRATION.md](INNER_MAPPER_INTEGRATION.md) for Inner Mapper setup

---

## 📡 Telnet Protocol

### Simple Request-Response

```
Request:  STATUS\r\n
Response: PAPER_OK\r\n
```

### Possible Responses

| Response | Meaning | Action |
|----------|---------|--------|
| `PAPER_OK` | Paper is present | Resume normal operation |
| `OUT_OF_PAPER` | Paper has run out | Request refill |
| `SENSOR_ERROR` | Sensor disconnected/error | Check hardware |
| `INITIALIZING` | System starting up | Retry after 5 seconds |
| `UNKNOWN_COMMAND` | Invalid command sent | Check request format |

### Example Session

```bash
$ telnet 192.168.1.100 2323
Trying 192.168.1.100...
Connected to 192.168.1.100.
Escape character is '^]'.
STATUS
PAPER_OK
Connection closed by foreign host.
```

---

## 🔧 Configuration

### Main Configuration Variables

Edit `/opt/printer_monitor/printer_monitor.py` (lines 1-60):

```python
# GPIO PINS
SENSOR_PIN = 17                    # Sensor input pin
GREEN_LED_PIN = 27                 # Green LED output
RED_LED_PIN = 22                   # Red LED output
USE_LEDS = True                    # Enable LED indicators

# SENSOR
DEBOUNCE_COUNT = 5                 # Stable readings before state change
SENSOR_READ_INTERVAL = 0.5         # Read every 0.5 seconds
SENSOR_TIMEOUT = 10                # Error if no read for 10 seconds

# TELNET SERVER
TELNET_PORT = 23                   # Port (or 2323 if no root)
LISTEN_ADDRESS = "0.0.0.0"         # Listen on all interfaces
MAX_CONCURRENT_CLIENTS = 5         # Max simultaneous connections

# LOGGING
LOG_FILE_PATH = "/var/log/printer_monitor.log"
LOG_LEVEL = logging.INFO

# FEATURES
DEBUG_MODE = False                 # Simulate without hardware
SIMULATE_PAPER_OUT = False         # Simulate paper-out condition
ENABLE_HEARTBEAT_LOGGING = True    # Log periodic status
```

### Quick Configuration Changes

**Use alternative Telnet port (non-root):**
```python
TELNET_PORT = 2323
```

**Disable LED indicators:**
```python
USE_LEDS = False
```

**Increase sensor sensitivity (faster response):**
```python
DEBOUNCE_COUNT = 3
SENSOR_READ_INTERVAL = 0.2
```

**Test without hardware:**
```python
DEBUG_MODE = True
SIMULATE_PAPER_OUT = False  # or True to simulate paper out
```

---

## 📊 System Status and Monitoring

### View Real-Time Logs

```bash
# Follow live logs
sudo journalctl -u printer_monitor -f

# Last 50 lines
sudo journalctl -u printer_monitor -n 50

# Errors only
sudo journalctl -u printer_monitor -p err
```

### Check Service Health

```bash
# Service status
sudo systemctl status printer_monitor

# Is service running?
systemctl is-active printer_monitor

# Resource usage
top -b -n 1 | grep printer_monitor

# Network listening
sudo ss -tlnp | grep python3
```

### Manual Status Test

```bash
# Local test
echo "STATUS" | nc localhost 2323

# Remote test (from Inner Mapper)
echo "STATUS" | nc 192.168.1.100 2323

# Full telnet session
telnet 192.168.1.100 2323
STATUS
quit
```

---

## 🐛 Debugging and Testing

### Debug Mode (No Hardware Required)

```bash
# Edit printer_monitor.py
DEBUG_MODE = True

# Restart service
sudo systemctl restart printer_monitor

# Check logs
sudo journalctl -u printer_monitor -f | grep -i "debug\|simulation"
```

### Simulate Paper-Out Condition

```bash
# Edit printer_monitor.py
DEBUG_MODE = True
SIMULATE_PAPER_OUT = True

# Restart service
sudo systemctl restart printer_monitor

# Test
echo "STATUS" | nc localhost 2323
# Should respond: OUT_OF_PAPER
```

### Manual GPIO Testing

```bash
# Read sensor directly
gpio -g read 17

# Toggle green LED
gpio -g mode 27 out
gpio -g write 27 1  # ON
gpio -g write 27 0  # OFF

# Check all GPIO pins
gpio readall
```

### Test Inner Mapper Integration

```bash
# From Inner Mapper machine
#!/bin/bash
for i in {1..5}; do
    echo "Poll $i:"
    echo "STATUS" | timeout 2 nc 192.168.1.100 2323
    sleep 1
done
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [INSTALLATION.md](INSTALLATION.md) | Step-by-step installation and setup |
| [WIRING_GUIDE.md](WIRING_GUIDE.md) | Hardware wiring and GPIO configuration |
| [INNER_MAPPER_INTEGRATION.md](INNER_MAPPER_INTEGRATION.md) | Inner Mapper polling and integration |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and solutions |

---

## 🏗️ Project Structure

```
/opt/printer_monitor/
├── printer_monitor.py              # Main application (800+ lines)
├── requirements.txt                # Python dependencies
├── printer_monitor.service         # systemd service file
├── README.md                       # This file
├── INSTALLATION.md                 # Installation guide
├── WIRING_GUIDE.md                # GPIO wiring instructions
├── INNER_MAPPER_INTEGRATION.md    # Inner Mapper setup
├── TROUBLESHOOTING.md             # Troubleshooting guide
├── test_monitor.py                # Unit tests (optional)
├── webhook_integration.py          # Webhook alerts (optional)
└── rest_api.py                    # REST API extension (optional)
```

---

## 🔐 Security

### Network Security

1. **Restrict Telnet access to specific IPs:**
```bash
sudo ufw allow from 192.168.1.50 to any port 2323
sudo ufw deny to any port 2323
```

2. **Use VPN for remote access:**
   - Telnet transmits in plaintext
   - For remote connections, use SSH tunnel or VPN

3. **Monitor access logs:**
```bash
sudo journalctl -u printer_monitor | grep "Client connected"
```

### Hardware Security

1. **GPIO access via pigpio daemon** (non-root)
2. **Service runs as `pi` user** (not root)
3. **Filesystem permissions:**
```bash
sudo chmod 640 /var/log/printer_monitor.log
sudo chown pi:pi /opt/printer_monitor
```

---

## ⚡ Performance

### Resource Usage

- **Memory:** ~40-50 MB at idle
- **CPU:** <1% on idle, <5% during sensor reads
- **Network:** ~200 bytes per status query
- **Disk I/O:** Minimal (logging to systemd journal)

### Optimization Tips

**For faster response:**
```python
DEBOUNCE_COUNT = 3          # Reduce from 5
SENSOR_READ_INTERVAL = 0.1  # Reduce from 0.5
```

**For lower resource usage:**
```python
SENSOR_READ_INTERVAL = 2.0   # Increase from 0.5
HEARTBEAT_INTERVAL = 600    # Increase from 60
ENABLE_HEARTBEAT_LOGGING = False
USE_LEDS = False
```

---

## 🚦 Status Codes

### Service Status
- **`active (running)`** - System operational, monitoring sensor
- **`inactive (dead)`** - Service stopped
- **`failed`** - Service crashed or error

### Paper Status
- **`PAPER_OK`** - Paper present, no action needed
- **`OUT_OF_PAPER`** - Paper depleted, refill required
- **`SENSOR_ERROR`** - Hardware error, check connections
- **`INITIALIZING`** - Warming up (transient)

### Sensor Health
- **`healthy`** - Sensor responding normally
- **`disconnected`** - No readings for 10+ seconds
- **`error`** - GPIO read error

---

## 📦 Hardware Requirements

### Minimum Configuration
- Raspberry Pi 3B+ or newer
- Reflective light sensor (e.g., E18-D80NK)
- Jumper wires and breadboard
- Power supply (5V, 2A minimum)

### Recommended Configuration
- Raspberry Pi 4B (2GB RAM)
- IR/Visible light sensor with adjustable potentiometer
- Shielded cables for long sensor runs
- Case or enclosure for protection
- UPS backup power (optional)

### Optional Enhancements
- Green and red LEDs (330Ω resistor each)
- WiFi or wired Ethernet (wired recommended for reliability)
- Webhook capable monitoring system
- REST API client

---

## 🔄 Sensor Logic

### Detection Mechanism

```
Paper Present:
  ├─ Reflective backing plate is NOT visible to sensor
  ├─ Sensor does NOT detect reflection
  └─ GPIO 17 = LOW (0)  →  Status: PAPER_OK ✓

Paper Depleted:
  ├─ Paper stack is empty
  ├─ Reflective backing plate IS visible to sensor
  ├─ Sensor DETECTS reflection
  └─ GPIO 17 = HIGH (1)  →  Status: OUT_OF_PAPER ⚠️
```

### Debouncing

To avoid false positives from sensor noise:
- Requires 5 consecutive identical readings before state change
- Each read interval = 0.5 seconds
- Total stabilization time = ~2.5 seconds (5 × 0.5s)
- Configurable via `DEBOUNCE_COUNT`

---

## 🔗 API Examples

### Python Integration

```python
import socket

def get_printer_status(ip="192.168.1.100", port=2323, timeout=5):
    """Get printer paper status via Telnet."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        sock.send(b"STATUS\r\n")
        response = sock.recv(1024).decode().strip()
        sock.close()
        return response
    except Exception as e:
        return f"ERROR: {e}"

# Usage
status = get_printer_status()
print(f"Printer status: {status}")
```

### Bash Integration

```bash
#!/bin/bash
PI_IP="192.168.1.100"

STATUS=$(echo "STATUS" | timeout 5 nc $PI_IP 2323)

case $STATUS in
    "PAPER_OK")
        echo "Paper is present"
        ;;
    "OUT_OF_PAPER")
        echo "ALERT: Paper needs refill!"
        # Send notification
        ;;
    "SENSOR_ERROR")
        echo "ERROR: Sensor malfunction"
        ;;
esac
```

---

## 🎯 Common Use Cases

### Use Case 1: Basic Monitoring
- Inner Mapper polls Pi every 60 seconds
- Responds with current status
- No external notifications needed

### Use Case 2: Alert on Paper-Out
- When status = OUT_OF_PAPER
- Trigger email to operator
- Create service ticket

### Use Case 3: Status Dashboard
- Display real-time status on web dashboard
- Show historical data and trends
- Track refill frequency

### Use Case 4: Predictive Maintenance
- Track status change frequency
- Estimate paper consumption
- Predict when refill will be needed

---

## 🔮 Future Enhancements

### Planned Features
- [ ] REST API endpoint (JSON responses)
- [ ] MQTT broker integration
- [ ] Home Assistant/OpenHAB support
- [ ] Email alerts on state change
- [ ] Webhook triggers
- [ ] Web dashboard UI
- [ ] Historical data tracking
- [ ] Docker containerization
- [ ] Multi-printer support
- [ ] Mobile app integration

### In Development
- See [ROADMAP.md](ROADMAP.md) for detailed plans

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🤝 Support and Contribution

### Getting Help
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review logs: `sudo journalctl -u printer_monitor -f`
3. Run diagnostics (see Troubleshooting guide)
4. Contact support with diagnostic information

### Reporting Issues
- Provide complete diagnostic output
- Include relevant log entries
- Describe what you've already tried
- Specify your hardware and OS version

### Contributing
- Code contributions welcome
- Follow Python PEP 8 style guide
- Add tests for new features
- Update documentation

---

## 📞 Contact

**Support Email:** [Your Support Email]  
**Issue Tracker:** [GitHub Issues URL]  
**Documentation:** [Wiki URL]  

---

## 🎓 Learning Resources

### Raspberry Pi
- [Official Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [GPIO Pin Configuration](https://www.raspberrypi.org/documentation/usage/gpio/)
- [systemd Service Management](https://wiki.debian.org/systemd)

### Python and gpiozero
- [gpiozero Documentation](https://gpiozero.readthedocs.io/)
- [Python Socket Programming](https://docs.python.org/3/library/socket.html)
- [Python Logging](https://docs.python.org/3/library/logging.html)

### Networking
- [Telnet Protocol](https://tools.ietf.org/html/rfc854)
- [TCP/IP Basics](https://www.comptia.org/)

---

## 📊 Changelog

### Version 1.0.0 (2024-01-15)
- Initial production release
- Full Telnet server implementation
- Sensor monitoring with debouncing
- LED indicator support
- systemd service integration
- Comprehensive documentation

### Version 0.9.0 (2024-01-10)
- Beta release
- Core functionality complete
- Initial testing complete

---

## 🏁 Quick Reference

### Service Commands
```bash
sudo systemctl start printer_monitor      # Start
sudo systemctl stop printer_monitor       # Stop
sudo systemctl restart printer_monitor    # Restart
sudo systemctl status printer_monitor     # Status
sudo systemctl enable printer_monitor     # Enable on boot
```

### Testing
```bash
# Test without hardware
DEBUG_MODE = True in printer_monitor.py
sudo systemctl restart printer_monitor

# Test Telnet
telnet localhost 2323
# or
echo "STATUS" | nc localhost 2323
```

### Logs
```bash
# Real-time
sudo journalctl -u printer_monitor -f

# Search
sudo journalctl -u printer_monitor | grep "ERROR"
```

### Configuration
```bash
# Edit config
nano /opt/printer_monitor/printer_monitor.py

# Apply changes
sudo systemctl restart printer_monitor
```

---

**For detailed setup instructions, see [INSTALLATION.md](INSTALLATION.md)**

**For hardware wiring, see [WIRING_GUIDE.md](WIRING_GUIDE.md)**

**For Inner Mapper integration, see [INNER_MAPPER_INTEGRATION.md](INNER_MAPPER_INTEGRATION.md)**

**For troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

---

**Last Updated:** January 2024  
**Tested On:** Raspberry Pi 4B with Raspberry Pi OS Bookworm  
**Python Version:** 3.9+  
**Status:** Production Ready ✓
