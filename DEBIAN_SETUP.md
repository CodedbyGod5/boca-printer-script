# Printer Monitor Setup for Debian GNU/Linux 13 (Trixie)

## Overview

This guide walks through installing the Printer Monitor on Debian GNU/Linux 13. The code is now fully compatible with Debian systems and will handle differences between Debian and other Linux distributions automatically.

## System Requirements

- **OS**: Debian GNU/Linux 13 (Trixie) or any systemd-based Debian derivative
- **Python**: Python 3.8 or newer
- **Hardware**: (Optional) Raspberry Pi or compatible board with GPIO pins for sensor monitoring
- **Network**: Internet connection for initial setup

## Pre-Installation Checklist

```bash
# Check your Debian version
lsb_release -d

# Verify Python 3 is installed
python3 --version

# Check if running as regular user or root
whoami
```

## Installation Steps

### 1. Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Dependencies

```bash
# Install Python package manager
sudo apt install -y python3-pip

# Install requests library for webhook integration (optional)
pip3 install --user requests
```

### 3. For Raspberry Pi Users Only

If running on Raspberry Pi, install GPIO support:

```bash
sudo apt install -y python3-gpiozero
sudo apt install -y pigpio  # Optional but recommended for better reliability
```

### 4. Clone or Copy Your Code

```bash
# Option A: Copy files to your home directory
mkdir -p ~/printer-monitor
cd ~/printer-monitor
# Copy all .py files and requirements.txt here

# Option B: Install to /opt for system-wide access (requires sudo)
sudo mkdir -p /opt/printer-monitor
sudo chown $USER:$USER /opt/printer-monitor
cp -r ~/Desktop/boca\ printer\ script/* /opt/printer-monitor/
```

### 5. Install Python Requirements

```bash
cd ~/printer-monitor
pip3 install --user -r requirements.txt
```

### 6. Test in Simulation Mode

The monitor runs in **simulation mode** if GPIO hardware is unavailable. This is perfect for testing on non-Raspberry Pi systems:

```bash
# Start the monitor (will listen on port 2323)
python3 printer_monitor.py

# In another terminal, test the connection
telnet localhost 2323

# Send the STATUS command
STATUS

# Expected response: INITIALIZING or PAPER_OK
```

### 7. Enable Auto-Start as Service (Optional)

To run the monitor automatically on system boot:

```bash
# Copy service file to system directory
sudo cp printer_monitor.service /etc/systemd/system/printer-monitor@.service

# Enable for your current user
sudo systemctl enable printer-monitor@$USER.service
sudo systemctl start printer-monitor@$USER.service

# Check status
sudo systemctl status printer-monitor@$USER.service

# View logs
journalctl -u printer-monitor@$USER.service -f
```

## Configuration Guide

### Port Configuration

- **Default Port**: 2323 (non-privileged, no root needed)
- **Traditional Telnet Port**: 23 (requires root privileges)

To use port 23, start the service with root:

```bash
sudo python3 printer_monitor.py
```

Or modify `TELNET_PORT` in `printer_monitor.py`:

```python
TELNET_PORT = 23  # Requires root/sudo
```

### GPIO Configuration (Raspberry Pi)

Edit `printer_monitor.py` and modify these settings:

```python
# GPIO Pin Configuration
SENSOR_PIN = 17                    # Change if using different pin
GREEN_LED_PIN = 27                 # Change if desired
RED_LED_PIN = 22                   # Change if desired
USE_LEDS = True                    # Set False to disable LEDs
```

### Debug Mode

To test without hardware, edit `printer_monitor.py`:

```python
DEBUG_MODE = True                  # Simulates sensor readings
SIMULATE_PAPER_OUT = False         # Set True to simulate paper-out condition
```

### Logging Configuration

Logs are saved to:
- **Production**: `/var/log/printer_monitor.log` (if writable)
- **Fallback**: `~/printer_monitor.log` (home directory)

To view logs:

```bash
# Using journalctl (recommended for systemd services)
journalctl -u printer-monitor@$USER.service -f

# Or tail the log file directly
tail -f ~/printer_monitor.log
```

## Testing and Verification

### Test 1: Simulation Mode

```bash
python3 printer_monitor.py
# Should output: "Telnet server started on 0.0.0.0:2323"
```

### Test 2: Telnet Connection

```bash
# In another terminal
telnet localhost 2323
```

### Test 3: Status Query

Once connected via Telnet, send:

```
STATUS
```

Expected responses:
- `INITIALIZING` - System starting up
- `PAPER_OK` - Paper detected (no reflection)
- `OUT_OF_PAPER` - Paper depleted (reflection detected)
- `SENSOR_ERROR` - Hardware error

### Test 4: Run Tests

```bash
python3 test_monitor.py --help
python3 test_monitor.py --telnet-test
```

## Troubleshooting

### Issue: "Permission denied" on /var/log

**Cause**: Non-root user cannot write to /var/log

**Solution**: Logs will automatically fallback to `~/printer_monitor.log`

### Issue: "Cannot bind to port 2323"

**Cause**: Port already in use or permission issue

**Solution**:
```bash
# Find what's using the port
sudo lsof -i :2323

# Or modify TELNET_PORT to a different port
```

### Issue: "gpiozero not available" on non-Pi system

**Expected behavior**: This is normal on systems without GPIO hardware. The monitor runs in simulation mode.

### Issue: Service not starting

**Check logs**:
```bash
journalctl -u printer-monitor@$USER.service -n 50
```

**Verify service file syntax**:
```bash
sudo systemctl daemon-reload
sudo systemctl status printer-monitor@$USER.service
```

## Webhook Integration (Optional)

To set up alerts when paper status changes:

1. Edit `webhook_integration.py`:

```python
WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN"
WEBHOOK_ENABLED = True
PRINTER_IP = "localhost"
PRINTER_PORT = 2323
```

2. Run as a service:

```bash
# Test first
python3 webhook_integration.py

# Then set as cron job or systemd service
```

## Security Notes

- **Port 2323**: Non-privileged (runs without sudo)
- **Port 23**: Requires root/sudo privileges
- **Log Files**: Check permissions if storing sensitive information
- **Webhooks**: Use HTTPS endpoints for webhook URLs
- **Network**: Consider firewall rules for Telnet access

## Uninstallation

To remove the printer monitor:

```bash
# Stop service if running
sudo systemctl stop printer-monitor@$USER.service
sudo systemctl disable printer-monitor@$USER.service

# Remove files
rm -rf ~/printer-monitor

# Remove service file
sudo rm /etc/systemd/system/printer-monitor@.service
sudo systemctl daemon-reload
```

## Additional Resources

- [Debian Documentation](https://www.debian.org/doc/)
- [systemd Documentation](https://www.freedesktop.org/software/systemd/man/)
- [gpiozero Documentation](https://gpiozero.readthedocs.io/)

## Support

For issues or questions:
1. Check `TROUBLESHOOTING.md`
2. Review application logs with `journalctl`
3. Test with `test_monitor.py`
4. Run in DEBUG_MODE for diagnostics

---

**Last Updated**: June 2026  
**Debian Version**: 13 (Trixie)  
**Python Version**: 3.8+
