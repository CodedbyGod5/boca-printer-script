# Inner Mapper Integration Guide

## Overview

This guide explains how to configure **Inner Mapper** to poll the **Raspberry Pi Printer Monitor** for paper status updates every 60 seconds via Telnet.

**Architecture Reminder:**
- **Raspberry Pi**: Acts as Telnet SERVER (listens on port 23 or 2323)
- **Inner Mapper**: Acts as Telnet CLIENT (connects every 60 seconds)
- **Protocol**: Simple text-based Telnet with STATUS request/response

---

## Prerequisites

1. Raspberry Pi Printer Monitor is running and accessible on network
2. Telnet port is open (default 23 or alternative 2323)
3. Inner Mapper has network connectivity to Raspberry Pi
4. Both systems are on same network (or VPN if remote)

---

## Step 1: Verify Connectivity

Before configuring Inner Mapper, ensure the Telnet service is accessible:

### Test from Inner Mapper Machine

#### Option A: Using telnet command
```bash
telnet 192.168.1.100 23
# or
telnet 192.168.1.100 2323
```

Expected output:
```
Trying 192.168.1.100...
Connected to 192.168.1.100.
Escape character is '^]'.
```

Type `STATUS` and press Enter:
```
STATUS
PAPER_OK
```

#### Option B: Using netcat (if telnet unavailable)
```bash
echo "STATUS" | nc 192.168.1.100 23
```

Expected output:
```
PAPER_OK
```

#### Option C: Using PowerShell (Windows Inner Mapper)
```powershell
$socket = New-Object System.Net.Sockets.TcpClient
$socket.Connect("192.168.1.100", 23)
$stream = $socket.GetStream()
$writer = New-Object System.IO.StreamWriter($stream)
$reader = New-Object System.IO.StreamReader($stream)
$writer.WriteLine("STATUS")
$writer.Flush()
$response = $reader.ReadLine()
Write-Host "Response: $response"
$socket.Close()
```

### Troubleshooting Connectivity

If connection fails:

```bash
# Check if Raspberry Pi is reachable
ping 192.168.1.100

# Check if port is open from Inner Mapper machine
sudo netstat -tlnp | grep -i listen  # On source
sudo ss -tulnp | grep :23             # Alternative

# Check firewall rules
sudo ufw status
sudo ufw allow from <inner-mapper-ip> to any port 23

# Check if service is running on Pi
ssh pi@192.168.1.100 'sudo systemctl status printer_monitor'
```

---

## Step 2: Understand Telnet Protocol

### Telnet Status Request Format

**Request:**
```
STATUS\r\n
```

**Possible Responses:**
```
PAPER_OK\r\n           # Paper is present
OUT_OF_PAPER\r\n       # Paper has run out
SENSOR_ERROR\r\n       # Sensor is disconnected/malfunctioning
INITIALIZING\r\n       # System still starting up (transient)
UNKNOWN_COMMAND\r\n    # Invalid command sent
```

### Connection Behavior

- TCP socket remains open until client closes
- Server closes after sending response
- Timeout: 10 seconds (if no activity)
- Maximum concurrent clients: 5

---

## Step 3: Inner Mapper Configuration

### Configuration File Format

Inner Mapper needs to connect to the Telnet server. Here are common integration patterns:

#### Pattern A: Custom Integration Script

If Inner Mapper supports custom scripts or plugins:

**Python Script Example:**
```python
#!/usr/bin/env python3
"""
Inner Mapper Printer Status Poller
Polls Raspberry Pi Printer Monitor every 60 seconds
"""

import socket
import time
import logging
from datetime import datetime

# Configuration
PRINTER_IP = "192.168.1.100"
PRINTER_PORT = 23  # or 2323 if default fails
POLL_INTERVAL = 60  # seconds

# Setup logging
logging.basicConfig(
    filename="/var/log/inner_mapper/printer_status.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def poll_printer_status():
    """
    Poll Raspberry Pi Printer Monitor for paper status.
    
    Returns:
        str: Status response (PAPER_OK, OUT_OF_PAPER, SENSOR_ERROR, etc)
    """
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 second timeout
        
        # Connect to Telnet server
        sock.connect((PRINTER_IP, PRINTER_PORT))
        
        # Send STATUS request
        sock.send(b"STATUS\r\n")
        
        # Receive response (up to 1024 bytes)
        response = sock.recv(1024).decode('utf-8').strip()
        
        # Close connection
        sock.close()
        
        return response
        
    except socket.timeout:
        error_msg = f"Timeout connecting to printer at {PRINTER_IP}:{PRINTER_PORT}"
        logging.error(error_msg)
        return "COMMUNICATION_TIMEOUT"
        
    except ConnectionRefusedError:
        error_msg = f"Connection refused by {PRINTER_IP}:{PRINTER_PORT}"
        logging.error(error_msg)
        return "CONNECTION_REFUSED"
        
    except Exception as e:
        logging.error(f"Error polling printer: {e}")
        return "ERROR"

def process_status(status):
    """
    Process status response and trigger Inner Mapper actions.
    
    Args:
        status (str): Status from printer monitor
    """
    if status == "PAPER_OK":
        logging.info("Printer: Paper OK - normal operation")
        # TODO: Update Inner Mapper state to NORMAL
        # TODO: Clear any OUT_OF_PAPER alerts
        
    elif status == "OUT_OF_PAPER":
        logging.warning("Printer: OUT OF PAPER - alert required")
        # TODO: Update Inner Mapper state to ALERT
        # TODO: Trigger refill notification
        # TODO: Notify printer operator
        
    elif status == "SENSOR_ERROR":
        logging.error("Printer: SENSOR ERROR - check hardware")
        # TODO: Update Inner Mapper state to ERROR
        # TODO: Trigger maintenance alert
        
    else:
        logging.warning(f"Printer: Unknown status - {status}")
        # TODO: Handle unexpected responses

def main():
    """Main polling loop."""
    logging.info("Printer Monitor Poller started")
    
    while True:
        try:
            # Poll printer status
            status = poll_printer_status()
            
            # Process response
            process_status(status)
            
            # Wait before next poll
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            logging.info("Poller stopped by user")
            break
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
```

**Install as systemd service:**
```bash
# Copy script to Inner Mapper server
sudo cp printer_monitor_poller.py /opt/inner_mapper/

# Create systemd service file
sudo cat > /etc/systemd/system/inner_mapper_printer_poller.service << EOF
[Unit]
Description=Inner Mapper Printer Status Poller
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/inner_mapper/printer_monitor_poller.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl enable inner_mapper_printer_poller
sudo systemctl start inner_mapper_printer_poller
```

#### Pattern B: Bash Script Integration

If Inner Mapper has webhook or event trigger capability:

```bash
#!/bin/bash
# Monitor printer status and update Inner Mapper

PRINTER_IP="192.168.1.100"
PRINTER_PORT="23"
INNER_MAPPER_API="http://localhost:8080/api"
POLL_INTERVAL=60

while true; do
    # Get printer status via Telnet
    STATUS=$(echo "STATUS" | timeout 5 nc $PRINTER_IP $PRINTER_PORT 2>/dev/null)
    
    case $STATUS in
        "PAPER_OK")
            echo "[$(date)] Paper OK - notifying Inner Mapper"
            curl -s "$INNER_MAPPER_API/printer/status" \
                -X POST \
                -H "Content-Type: application/json" \
                -d '{"status":"ready","timestamp":"'"$(date -Iseconds)"'"}'
            ;;
        "OUT_OF_PAPER")
            echo "[$(date)] Paper OUT - notifying Inner Mapper"
            curl -s "$INNER_MAPPER_API/printer/alert" \
                -X POST \
                -H "Content-Type: application/json" \
                -d '{"alert":"paper_out","severity":"warning","timestamp":"'"$(date -Iseconds)"'"}'
            ;;
        "SENSOR_ERROR")
            echo "[$(date)] Sensor ERROR - notifying Inner Mapper"
            curl -s "$INNER_MAPPER_API/printer/alert" \
                -X POST \
                -H "Content-Type: application/json" \
                -d '{"alert":"sensor_error","severity":"critical","timestamp":"'"$(date -Iseconds)"'"}'
            ;;
        *)
            echo "[$(date)] Unknown status: $STATUS"
            ;;
    esac
    
    sleep $POLL_INTERVAL
done
```

#### Pattern C: Direct Inner Mapper Configuration

If Inner Mapper has built-in device polling:

**Configuration Example (pseudo-config):**
```yaml
devices:
  - name: "Boca Printer Monitor"
    type: "telnet_device"
    host: "192.168.1.100"
    port: 23
    
    polling:
      enabled: true
      interval: 60  # seconds
      timeout: 10   # seconds
      
    commands:
      status:
        send: "STATUS"
        expected_responses:
          - "PAPER_OK"
          - "OUT_OF_PAPER"
          - "SENSOR_ERROR"
        
    alerts:
      - condition: "response == OUT_OF_PAPER"
        action: "notify"
        recipients: ["operator@company.com"]
        message: "Printer out of paper - refill required"
        
      - condition: "response == SENSOR_ERROR"
        action: "notify"
        recipients: ["maintenance@company.com"]
        message: "Printer sensor error - hardware check required"
```

---

## Step 4: State Management in Inner Mapper

### Recommended State Handling

```python
class PrinterState:
    """Inner Mapper printer state manager."""
    
    STATES = {
        "PAPER_OK": {
            "display": "Ready",
            "color": "green",
            "alert": False,
            "action": "NONE"
        },
        "OUT_OF_PAPER": {
            "display": "Out of Paper",
            "color": "red",
            "alert": True,
            "action": "REFILL_REQUEST"
        },
        "SENSOR_ERROR": {
            "display": "Sensor Error",
            "color": "red",
            "alert": True,
            "action": "MAINTENANCE_REQUEST"
        },
        "INITIALIZING": {
            "display": "Starting",
            "color": "yellow",
            "alert": False,
            "action": "NONE"
        },
        "COMMUNICATION_ERROR": {
            "display": "Unreachable",
            "color": "orange",
            "alert": True,
            "action": "NETWORK_CHECK"
        }
    }
    
    def __init__(self):
        self.current_state = "INITIALIZING"
        self.last_update = None
        self.consecutive_failures = 0
        
    def update(self, new_state):
        """Update printer state."""
        if new_state != self.current_state:
            self.consecutive_failures = 0
            self.current_state = new_state
            self.last_update = datetime.now()
            self._trigger_state_change(new_state)
        
    def on_communication_error(self):
        """Handle communication failures with backoff."""
        self.consecutive_failures += 1
        if self.consecutive_failures >= 3:
            self.current_state = "COMMUNICATION_ERROR"
            self._trigger_state_change("COMMUNICATION_ERROR")
    
    def _trigger_state_change(self, state):
        """Trigger Inner Mapper actions on state change."""
        state_info = self.STATES.get(state, {})
        
        # Update UI
        self.update_ui(state_info["display"], state_info["color"])
        
        # Handle alerts
        if state_info["alert"]:
            self.trigger_alert(state)
        
        # Execute action
        self.execute_action(state_info["action"], state)
    
    def update_ui(self, display, color):
        """Update Inner Mapper UI display."""
        # Send to Inner Mapper API
        pass
    
    def trigger_alert(self, state):
        """Send alerts based on state."""
        if state == "OUT_OF_PAPER":
            self.send_email_alert(
                subject="Printer Paper Refill Needed",
                recipients=["operator@company.com"],
                body="The Boca printer has run out of paper. Please refill."
            )
        elif state == "SENSOR_ERROR":
            self.send_email_alert(
                subject="Printer Sensor Error - Maintenance Required",
                recipients=["maintenance@company.com"],
                body="The printer sensor is not responding. Hardware check required."
            )
    
    def execute_action(self, action, state):
        """Execute automated actions."""
        if action == "REFILL_REQUEST":
            # Create work order, send notification
            pass
        elif action == "MAINTENANCE_REQUEST":
            # Escalate to maintenance
            pass
```

---

## Step 5: Error Handling and Recovery

### Connection Retry Logic

```python
def poll_with_retry(max_retries=3, backoff_seconds=5):
    """Poll with exponential backoff retry."""
    
    for attempt in range(max_retries):
        try:
            return poll_printer_status()
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = backoff_seconds * (2 ** attempt)
                logging.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                logging.error(f"All {max_retries} attempts failed")
                return "COMMUNICATION_ERROR"
```

### Timeout Handling

**Recommended timeouts:**
- Socket timeout: 10 seconds
- Poll interval: 60 seconds
- Retry wait: 5-15 seconds (exponential backoff)
- Max consecutive failures before alert: 3 (means 3 minutes of failure)

---

## Step 6: Logging and Monitoring

### Log File Configuration

Place polling logs in accessible location:
```bash
/var/log/inner_mapper/printer_poller.log
```

### Log Format Example

```
2024-01-15 14:00:00 - INFO - Printer status: PAPER_OK
2024-01-15 14:01:00 - INFO - Printer status: PAPER_OK
2024-01-15 14:02:00 - WARNING - Printer status: OUT_OF_PAPER - alert triggered
2024-01-15 14:03:00 - INFO - Operator notified of paper refill requirement
2024-01-15 14:04:00 - INFO - Printer status: PAPER_OK - alert cleared
```

### Monitoring Queries

```bash
# Last status update
tail -1 /var/log/inner_mapper/printer_poller.log

# Check error frequency
grep -c "ERROR" /var/log/inner_mapper/printer_poller.log

# Monitor communication issues
grep "timeout\|refused\|error" /var/log/inner_mapper/printer_poller.log

# Real-time monitoring
tail -f /var/log/inner_mapper/printer_poller.log | grep --color=auto "OUT_OF_PAPER\|ERROR"
```

---

## Step 7: Testing Configuration

### Unit Test Example

```python
import unittest
from unittest.mock import patch, MagicMock

class TestPrinterPoller(unittest.TestCase):
    
    def test_status_response_parsing(self):
        """Test parsing of various status responses."""
        test_cases = [
            ("PAPER_OK\r\n", "PAPER_OK"),
            ("OUT_OF_PAPER\r\n", "OUT_OF_PAPER"),
            ("SENSOR_ERROR\r\n", "SENSOR_ERROR"),
        ]
        
        for response, expected in test_cases:
            status = response.strip()
            self.assertEqual(status, expected)
    
    def test_timeout_handling(self):
        """Test timeout handling."""
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect.side_effect = socket.timeout
            mock_socket.return_value = mock_instance
            
            result = poll_printer_status()
            self.assertEqual(result, "COMMUNICATION_TIMEOUT")
    
    def test_connection_refused_handling(self):
        """Test connection refused handling."""
        with patch('socket.socket') as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect.side_effect = ConnectionRefusedError
            mock_socket.return_value = mock_instance
            
            result = poll_printer_status()
            self.assertEqual(result, "CONNECTION_REFUSED")
```

### Integration Test

```bash
#!/bin/bash
# Integration test script

echo "Testing Printer Monitor Integration..."

# Test 1: Network connectivity
echo "Test 1: Network connectivity"
if ping -c 1 192.168.1.100 &> /dev/null; then
    echo "✓ Ping successful"
else
    echo "✗ Cannot reach printer IP"
    exit 1
fi

# Test 2: Telnet connectivity
echo "Test 2: Telnet connectivity"
result=$(echo "STATUS" | timeout 3 nc 192.168.1.100 23 2>/dev/null)
if [ -n "$result" ]; then
    echo "✓ Telnet responsive: $result"
else
    echo "✗ No Telnet response"
    exit 1
fi

# Test 3: Valid response
echo "Test 3: Valid status response"
if [[ "$result" =~ ^(PAPER_OK|OUT_OF_PAPER|SENSOR_ERROR|INITIALIZING)$ ]]; then
    echo "✓ Valid response format: $result"
else
    echo "✗ Invalid response format: $result"
    exit 1
fi

echo "All tests passed!"
```

---

## Troubleshooting

### Common Issues

#### Issue: Connection Refused
**Cause:** Printer Monitor service not running or port wrong

**Solution:**
```bash
# Verify service is running on Pi
ssh pi@192.168.1.100 'sudo systemctl status printer_monitor'

# Check port number
ssh pi@192.168.1.100 'sudo netstat -tlnp | grep python'

# Verify firewall allows connection
ssh pi@192.168.1.100 'sudo ufw allow from <inner-mapper-ip> to any port 23'
```

#### Issue: Timeout
**Cause:** Network latency, firewall filtering, or service unresponsive

**Solution:**
```bash
# Test network path
traceroute 192.168.1.100

# Increase timeout in Inner Mapper configuration (to 15-20 seconds)

# Check for packet loss
ping -c 20 192.168.1.100 | grep loss
```

#### Issue: Intermittent Connectivity
**Cause:** Wi-Fi interference, network congestion

**Solution:**
- Use wired Ethernet for Raspberry Pi (recommended for production)
- Increase poll interval if no more than 60-second latency acceptable
- Implement connection pooling to reduce reconnect overhead

---

## Security Considerations

### Telnet Security Warning

**IMPORTANT:** Telnet transmits credentials in plaintext and is not secure for sensitive environments.

### Recommended Security Measures

1. **Network Isolation**
   ```bash
   # Restrict Telnet access to specific Inner Mapper IP
   sudo ufw delete allow 23/tcp
   sudo ufw allow from 192.168.1.50 to any port 23
   ```

2. **VPN Access (for remote monitoring)**
   ```bash
   # If Inner Mapper is remote, use VPN tunnel
   # Telnet through SSH tunnel example:
   ssh -L 23:192.168.1.100:23 user@vpn-gateway
   telnet localhost 23
   ```

3. **Firewall Rules**
   ```bash
   # Only allow Inner Mapper to connect
   sudo iptables -A INPUT -p tcp --dport 23 -s 192.168.1.50 -j ACCEPT
   sudo iptables -A INPUT -p tcp --dport 23 -j DROP
   ```

4. **Optional: Authentication Layer**
   - Consider wrapping Telnet with custom authentication
   - Or move to REST API with token-based auth (future enhancement)

---

## Monitoring and Dashboards

### Example Grafana Integration

If using Grafana for monitoring:

```json
{
  "dashboard": {
    "title": "Boca Printer Status",
    "panels": [
      {
        "title": "Paper Status",
        "type": "stat",
        "targets": [
          {
            "expr": "printer_status{type='paper'}",
            "legendFormat": "{{status}}"
          }
        ]
      },
      {
        "title": "Status Changes (24h)",
        "type": "graph",
        "targets": [
          {
            "expr": "increase(printer_status_changes[24h])"
          }
        ]
      }
    ]
  }
}
```

---

## Next Steps

1. **Deploy Integration Script**
   - Copy chosen pattern (Python/Bash/Config) to Inner Mapper
   - Configure with correct Raspberry Pi IP and port

2. **Set Up Logging**
   - Create log directory on Inner Mapper
   - Configure log rotation

3. **Test End-to-End**
   - Verify polling every 60 seconds
   - Confirm alerts trigger on paper out
   - Test recovery when paper is refilled

4. **Monitor Production**
   - Set up alerting on integration failures
   - Track poll response times
   - Monitor sensor error rate

---

## Support and Escalation

### Troubleshooting Resources

- Raspberry Pi Printer Monitor logs: `/var/log/printer_monitor.log`
- Inner Mapper integration logs: `/var/log/inner_mapper/printer_poller.log`
- Network diagnostics: Use `ping`, `traceroute`, `netstat`, `nmap`

### Escalation Path

1. **Level 1:** Check network connectivity and service status
2. **Level 2:** Review logs and verify configuration
3. **Level 3:** Check GPIO wiring and sensor health on Pi
4. **Level 4:** Contact Printer Monitor development team

---

**Document Version:** 1.0
**Last Updated:** 2024
**Compatible With:** Printer Monitor v1.0+
