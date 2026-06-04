# Boca Printer Paper Monitor - Complete File Guide

## 📁 Project Structure

```
/opt/printer_monitor/
│
├── 🟢 CORE APPLICATION
│   ├── printer_monitor.py                 # Main Telnet server (850+ lines)
│   ├── requirements.txt                   # Python dependencies
│   └── printer_monitor.service            # systemd service file
│
├── 📚 DOCUMENTATION
│   ├── README.md                          # Quick start & overview
│   ├── INSTALLATION.md                    # Detailed setup guide
│   ├── WIRING_GUIDE.md                    # Hardware wiring instructions
│   ├── INNER_MAPPER_INTEGRATION.md       # Inner Mapper polling setup
│   ├── TROUBLESHOOTING.md                 # Common issues & solutions
│   ├── FILE_GUIDE.md                      # This file
│   └── ROADMAP.md                         # Future enhancements
│
├── 🔧 OPTIONAL FEATURES
│   ├── webhook_integration.py             # Discord/Slack alert webhooks
│   ├── rest_api.py                        # HTTP/JSON API interface
│   └── test_monitor.py                    # Testing & diagnostics tool
│
└── 📋 CONFIGURATION
    └── printer_monitor.py (lines 1-60)   # Configuration variables
```

---

## 📄 File Descriptions

### Core Application Files

#### `printer_monitor.py` (Primary Application)

**Purpose:** Main Telnet server that monitors printer paper status

**Key Components:**
- `PaperMonitorLogger` - Logging with rotation
- `SensorManager` - GPIO sensor monitoring with debouncing
- `StateManager` - State machine for paper status
- `TelnetServer` - Telnet protocol server
- `LEDIndicator` - Optional LED control (GPIO 27, 22)
- `PrinterMonitor` - Main coordinator class

**Key Features:**
- Telnet listener on port 23 or 2323
- Sensor debouncing (5 consecutive stable reads)
- Automatic GPIO cleanup on shutdown
- Thread-safe client handling
- Enterprise logging to systemd journal
- Debug and simulation modes

**Configuration Variables (lines 1-60):**
```python
SENSOR_PIN = 17                  # GPIO pin for sensor
TELNET_PORT = 2323              # Telnet port (use 2323 if no root)
DEBOUNCE_COUNT = 5              # Stable reads required
USE_LEDS = True                 # Enable LED indicators
DEBUG_MODE = False              # Test without hardware
```

**Running:**
```bash
# As service
sudo systemctl start printer_monitor

# Directly (for debugging)
python3 /opt/printer_monitor/printer_monitor.py

# With debug mode
# Edit: DEBUG_MODE = True
# Then: sudo systemctl restart printer_monitor
```

---

#### `requirements.txt`

**Purpose:** Python package dependencies

**Contents:**
- `gpiozero>=2.0.0` - GPIO abstraction layer
- `pigpio>=1.78` - GPIO daemon
- `requests>=2.28.0` - HTTP requests (optional, for webhooks)
- `Flask>=2.3.0` - Web framework (optional, for REST API)

**Installation:**
```bash
pip3 install -r requirements.txt
```

---

#### `printer_monitor.service`

**Purpose:** systemd service configuration for auto-startup

**Key Settings:**
- `User=pi` - Runs as pi user (non-root)
- `Restart=on-failure` - Auto-restart on crash
- `After=network-online.target` - Starts after network
- `MemoryLimit=256M` - Resource limit
- `CPUQuota=50%` - CPU usage limit

**Installation:**
```bash
sudo cp printer_monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable printer_monitor
sudo systemctl start printer_monitor
```

---

### Documentation Files

#### `README.md` (Overview & Quick Start)

**Sections:**
1. Overview & key features
2. 5-minute quick start
3. Telnet protocol reference
4. Configuration guide
5. API examples
6. Security considerations
7. Performance optimization
8. Support & resources

**Use This When:**
- First-time setup
- Need quick reference
- Looking for feature overview
- Checking API protocol

---

#### `INSTALLATION.md` (Detailed Setup)

**Sections:**
1. Prerequisites & hardware requirements
2. Step-by-step installation (8 steps)
3. Configuration variable guide
4. Systemd service management
5. Telnet protocol reference
6. Testing procedures
7. Log management
8. Performance tuning
9. GPIO pin reference table
10. Common issues quick fixes
11. Security hardening

**Content:** ~800 lines with bash commands

**Use This When:**
- Setting up on Raspberry Pi
- Troubleshooting installation
- Configuring service parameters
- Managing logs

---

#### `WIRING_GUIDE.md` (Hardware Setup)

**Sections:**
1. Component specifications
2. GPIO reference table
3. Wiring diagrams (ASCII art)
4. Breadboard layout examples
5. Step-by-step wiring instructions
6. Pin assignment summary
7. Advanced configuration (sensitivity, pull-up resistors)
8. Testing connections (multimeter procedures)
9. Troubleshooting
10. Component shopping list

**Includes:**
- Reflective sensor wiring
- LED indicator wiring
- GPIO pin layout (40-pin header)
- Safety warnings
- Maintenance instructions

**Use This When:**
- Connecting hardware
- Testing GPIO connections
- Verifying sensor orientation
- LED polarity issues

---

#### `INNER_MAPPER_INTEGRATION.md` (Polling & Integration)

**Sections:**
1. Architecture overview
2. Connectivity verification
3. Telnet protocol format
4. Inner Mapper configuration patterns
5. Python integration example (100+ lines)
6. Bash/cURL integration examples
7. State management examples
8. Error handling & retry logic
9. Logging setup
10. Testing & validation
11. Security measures
12. Monitoring & dashboards

**Includes:**
- 3 integration patterns (Python, Bash, Config)
- PowerShell example for Windows
- Webhook support
- Status response parsing
- Connection retry logic with backoff

**Use This When:**
- Configuring Inner Mapper
- Creating custom polling scripts
- Setting up notifications
- Integrating with other systems

---

#### `TROUBLESHOOTING.md` (Problem Solving)

**Sections:**
1. Quick reference table
2. Error messages and solutions (10+ common errors)
3. Diagnostic procedures
4. Common scenarios with fixes
5. Reset and recovery procedures
6. Performance tuning
7. Monitoring and alerting
8. Support resources

**Includes:**
- Complete diagnostic scripts
- GPIO testing procedures
- Log analysis examples
- Service recovery procedures
- Full system reset instructions

**Use This When:**
- Service won't start
- Sensor not responding
- Telnet connection issues
- CPU usage high
- LED not working
- Getting cryptic error messages

---

#### `FILE_GUIDE.md` (This Document)

**Purpose:** Index of all files and their purposes

**Sections:**
1. Project structure
2. File descriptions with usage
3. Quick reference commands
4. Configuration summary
5. Testing procedures
6. Deployment checklist

---

### Optional Feature Files

#### `webhook_integration.py` (Alert System)

**Purpose:** Send alerts to Discord, Slack, or generic webhooks

**Capabilities:**
- Polls printer monitor for status changes
- Formats alerts for Discord, Slack, or generic webhooks
- Runs as separate service
- Logs all webhook activity

**Configuration:**
```python
WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN"
WEBHOOK_ENABLED = True
```

**Running:**
```bash
# Standalone
python3 webhook_integration.py

# As systemd service (optional)
sudo systemctl start webhook_integration
```

**Use This When:**
- Want Discord/Slack alerts
- Need to notify team on paper-out
- Integrating with alerting systems

---

#### `rest_api.py` (HTTP API)

**Purpose:** Modern HTTP/JSON interface alongside Telnet

**Endpoints:**
- `GET /api/status` - Full status JSON
- `GET /api/status/paper` - Simplified response
- `GET /health` - Health check
- `GET /metrics` - Prometheus-compatible metrics
- `POST /webhook/discord` - Test webhook

**Running:**
```bash
python3 rest_api.py
# Listens on http://localhost:5000/
```

**Example Usage:**
```bash
curl http://localhost:5000/api/status
# Returns:
# {
#   "status": "PAPER_OK",
#   "paper_ok": true,
#   "last_update": "2024-01-15T14:30:00",
#   "errors": 0
# }
```

**Use This When:**
- Need HTTP/JSON interface
- Integrating with web applications
- Using Prometheus monitoring
- Modern API-first systems

---

#### `test_monitor.py` (Testing & Diagnostics)

**Purpose:** Comprehensive testing without running full service

**Test Types:**
- `--telnet-test` - Connection test
- `--polling-test` - Repeated polling with stats
- `--stress-test` - High-load testing
- `--gpio-test` - Hardware GPIO functionality
- `--system-test` - System diagnostics
- `--all` - Run all tests

**Usage Examples:**
```bash
# Test Telnet connectivity
python3 test_monitor.py --telnet-test

# Stress test for 30 seconds
python3 test_monitor.py --stress-test --duration 30

# Run all diagnostics
python3 test_monitor.py --all

# Custom IP and port
python3 test_monitor.py --telnet-test --ip 192.168.1.100 --port 2323
```

**Use This When:**
- Verifying installation
- Testing hardware
- Stress testing for reliability
- Collecting diagnostic information
- Troubleshooting issues

---

## ⚙️ Configuration Summary

### Essential Configuration (Must Change)

**File:** `printer_monitor.py` lines 1-60

```python
# GPIO PINS - Change to match your hardware
SENSOR_PIN = 17              # Reflective light sensor
GREEN_LED_PIN = 27           # Green LED (optional)
RED_LED_PIN = 22             # Red LED (optional)

# TELNET PORT - Change if port 23 unavailable
TELNET_PORT = 2323           # Use 2323 if no root access
```

### Optional Configuration

```python
# SENSOR - Adjust for your sensor behavior
DEBOUNCE_COUNT = 5           # Higher = more stable but slower
SENSOR_READ_INTERVAL = 0.5   # Higher = lower CPU usage

# FEATURES - Enable/disable functionality
USE_LEDS = True              # Disable if no LEDs
DEBUG_MODE = False           # Enable for testing without hardware
ENABLE_HEARTBEAT_LOGGING = True  # Disable to reduce log spam
```

---

## 🧪 Testing Procedures

### Quick Test (30 seconds)

```bash
# 1. Start service
sudo systemctl start printer_monitor

# 2. Test Telnet
echo "STATUS" | nc localhost 2323

# 3. Expected response
# PAPER_OK or OUT_OF_PAPER
```

### Full Diagnostic Test

```bash
# Run complete test suite
python3 test_monitor.py --all

# Or run individually:
python3 test_monitor.py --telnet-test
python3 test_monitor.py --polling-test --count 20
python3 test_monitor.py --gpio-test
python3 test_monitor.py --system-test
```

### Manual Service Test

```bash
# Check if running
sudo systemctl status printer_monitor

# View logs
sudo journalctl -u printer_monitor -f

# Manual Telnet
telnet localhost 2323
# Type: STATUS
# Press Enter
# Expected: PAPER_OK

# Test GPIO directly
gpio -g read 17     # Sensor
gpio -g write 27 1  # Green LED ON
gpio -g write 27 0  # Green LED OFF
```

---

## 📋 Deployment Checklist

### Pre-Deployment

- [ ] Raspberry Pi OS Bookworm installed and updated
- [ ] Sensor connected to GPIO 17
- [ ] LEDs connected to GPIO 27 and 22 (if using)
- [ ] All jumpers and cables secure
- [ ] Network connectivity verified

### Installation

- [ ] Python 3.9+ installed
- [ ] gpiozero and pigpio installed
- [ ] printer_monitor.py copied to /opt/printer_monitor/
- [ ] requirements.txt installed
- [ ] printer_monitor.service installed
- [ ] Permissions set correctly
- [ ] Service enabled with systemctl enable

### Testing

- [ ] Service starts without errors
- [ ] Telnet connectivity works
- [ ] Sensor responds to changes
- [ ] LEDs light up correctly (if enabled)
- [ ] Logs show proper operation
- [ ] Inner Mapper can poll successfully

### Production

- [ ] Firewall rules configured
- [ ] Logging rotation set up
- [ ] Monitoring/alerting configured
- [ ] Backup of configuration saved
- [ ] Documentation available to operators
- [ ] Support contacts listed

---

## 🔍 Quick Reference Commands

### Service Management

```bash
# Start/Stop
sudo systemctl start printer_monitor
sudo systemctl stop printer_monitor
sudo systemctl restart printer_monitor

# Status
sudo systemctl status printer_monitor
systemctl is-active printer_monitor

# Auto-start
sudo systemctl enable printer_monitor
sudo systemctl disable printer_monitor
```

### Testing

```bash
# Telnet test
telnet localhost 2323
echo "STATUS" | nc localhost 2323

# GPIO test
gpio -g read 17
gpio -g write 27 1

# Run diagnostics
python3 test_monitor.py --all
```

### Logging

```bash
# Real-time logs
sudo journalctl -u printer_monitor -f

# Recent logs
sudo journalctl -u printer_monitor -n 50

# Search logs
sudo journalctl -u printer_monitor | grep "error"

# Export logs
sudo journalctl -u printer_monitor > /tmp/logs.txt
```

### Troubleshooting

```bash
# Check service status
sudo systemctl status printer_monitor

# Check network listening
sudo ss -tlnp | grep python3

# Check GPIO pins
gpio readall

# Check pigpio
sudo systemctl status pigpiod
pigs hwver
```

---

## 🌐 File Locations Summary

| Component | Location | Permissions | Owner |
|-----------|----------|-------------|-------|
| Main script | `/opt/printer_monitor/printer_monitor.py` | 755 | pi:pi |
| Config | `/opt/printer_monitor/printer_monitor.py` lines 1-60 | 755 | pi:pi |
| Service file | `/etc/systemd/system/printer_monitor.service` | 644 | root:root |
| Log file | `/var/log/printer_monitor.log` | 640 | pi:pi |
| Python cache | `/opt/printer_monitor/__pycache__/` | - | pi:pi |

---

## 📖 Documentation Decision Tree

```
┌─ START HERE? ────→ README.md
│
├─ Setting up? ────→ INSTALLATION.md
│
├─ Wiring hardware? ─→ WIRING_GUIDE.md
│
├─ Configuring Inner Mapper? ─→ INNER_MAPPER_INTEGRATION.md
│
├─ Something broken? ─→ TROUBLESHOOTING.md
│
├─ What files are these? ─→ FILE_GUIDE.md (this file)
│
└─ Want advanced features? ─→ webhook_integration.py or rest_api.py
```

---

## 🚀 Next Steps

1. **Quick Start:** Read README.md (5 minutes)
2. **Installation:** Follow INSTALLATION.md step-by-step
3. **Hardware:** Use WIRING_GUIDE.md to connect sensor
4. **Testing:** Run test_monitor.py to verify
5. **Integration:** Configure Inner Mapper with INNER_MAPPER_INTEGRATION.md
6. **Monitoring:** Set up logging and alerting
7. **Troubleshooting:** Reference TROUBLESHOOTING.md as needed

---

## ✅ File Checklist

**Essential Files (Required):**
- [x] printer_monitor.py - Main application
- [x] requirements.txt - Dependencies
- [x] printer_monitor.service - systemd service

**Documentation (Recommended):**
- [x] README.md - Overview
- [x] INSTALLATION.md - Setup guide
- [x] WIRING_GUIDE.md - Hardware guide
- [x] INNER_MAPPER_INTEGRATION.md - Integration guide
- [x] TROUBLESHOOTING.md - Problem solving

**Optional Features:**
- [x] webhook_integration.py - Alerts
- [x] rest_api.py - HTTP API
- [x] test_monitor.py - Diagnostics

**This Document:**
- [x] FILE_GUIDE.md - File reference

---

**Document Version:** 1.0  
**Last Updated:** 2024-01-15  
**Total Documentation:** 5000+ lines  
**Files Included:** 14  
**Estimated Setup Time:** 30 minutes  
**Estimated Learning Time:** 1-2 hours  

---

For detailed information on any component, refer to the specific documentation file listed above.
