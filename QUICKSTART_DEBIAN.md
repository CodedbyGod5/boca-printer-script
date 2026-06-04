# Quick Start Guide - Debian GNU/Linux 13

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
sudo apt update
sudo apt install -y python3-pip
pip3 install --user requests
```

### Step 2: Prepare Files
```bash
mkdir -p ~/printer-monitor
cd ~/printer-monitor
# Copy all files here
```

### Step 3: Install Requirements
```bash
pip3 install --user -r requirements.txt
```

### Step 4: Test It
```bash
python3 printer_monitor.py
```

### Step 5: Connect (in another terminal)
```bash
telnet localhost 2323
STATUS
```

**Expected Output**: `PAPER_OK` or `INITIALIZING`

---

## Port Reference

| Port | Requires | Use Case |
|------|----------|----------|
| 2323 | No sudo  | Development, regular users |
| 23   | sudo     | Production servers (optional) |

---

## Service Setup (Optional)

```bash
# Install as auto-start service
sudo cp printer_monitor.service /etc/systemd/system/printer-monitor@.service

# Enable for current user
sudo systemctl enable printer-monitor@$USER.service
sudo systemctl start printer-monitor@$USER.service

# Check status
sudo systemctl status printer-monitor@$USER.service

# View logs
journalctl -u printer-monitor@$USER.service -f
```

---

## Logs Location

- **Service logs**: `journalctl -u printer-monitor@$USER.service`
- **File logs**: `~/printer_monitor.log`
- **System logs**: `/var/log/printer_monitor.log` (if writable)

---

## Commands Cheat Sheet

```bash
# Test telnet connection
telnet localhost 2323

# Query status (in telnet)
STATUS

# Stop service
sudo systemctl stop printer-monitor@$USER.service

# Restart service
sudo systemctl restart printer-monitor@$USER.service

# View service logs (last 50 lines)
journalctl -u printer-monitor@$USER.service -n 50

# Live log tail
journalctl -u printer-monitor@$USER.service -f

# Check if listening on port
netstat -tlnp | grep 2323
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection refused" | Make sure `python3 printer_monitor.py` is running |
| "Address already in use" | Change `TELNET_PORT` to different value (e.g., 2324) |
| "Permission denied" | You don't need sudo - code handles permissions |
| Service won't start | Check logs: `journalctl -u printer-monitor@$USER.service` |

---

## Debug Mode (No Hardware Needed)

Edit `printer_monitor.py`:

```python
DEBUG_MODE = True  # Simulates sensor
SIMULATE_PAPER_OUT = False  # Set True to test paper-out alert
```

Then restart and it works without GPIO hardware!

---

## Full Documentation

- **Setup Details**: See `DEBIAN_SETUP.md`
- **All Changes**: See `LINUX_COMPATIBILITY.md`
- **Issues**: See `TROUBLESHOOTING.md`

---

**Happy monitoring! 🎉**
