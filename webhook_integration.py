#!/usr/bin/env python3
"""
Optional: Webhook Integration for Printer Monitor Alerts
Sends webhook notifications when paper status changes

Usage:
    1. Edit WEBHOOK_URL to your webhook endpoint (Discord, Slack, etc)
    2. Run this script as a service or cron job
    3. It polls the printer monitor and sends alerts on state changes

Supported Webhooks:
    - Discord webhooks
    - Slack webhooks
    - Generic HTTP webhooks
    - Email via webhook gateway
"""

import requests
import time
import logging
import socket
import os
import sys
from datetime import datetime
from typing import Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

# Printer Monitor
PRINTER_IP = "localhost"
PRINTER_PORT = 2323
POLL_INTERVAL = 60  # seconds

# Webhook Configuration
# DISCORD EXAMPLE:
# WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"

# SLACK EXAMPLE:
# WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

# Generic HTTP:
WEBHOOK_URL = "http://localhost:8000/webhook"
WEBHOOK_ENABLED = False  # Set to True to enable

# Logging
# Will attempt /var/log first, fallback to home directory if not writable
LOG_FILE = "/var/log/printer_webhook.log"
LOG_LEVEL = logging.INFO

# ============================================================================
# LOGGER SETUP
# ============================================================================

# Determine actual log file path with fallback
_log_file = LOG_FILE
try:
    if not os.path.exists(os.path.dirname(_log_file)):
        os.makedirs(os.path.dirname(_log_file), mode=0o755, exist_ok=True)
    # Test write access
    with open(_log_file, 'a'):
        pass
except (OSError, PermissionError):
    # Fallback to home directory
    _log_file = os.path.expanduser("~/printer_webhook.log")
    print(f"Cannot write to {LOG_FILE}, using fallback: {_log_file}", file=sys.stderr)

logging.basicConfig(
    filename=_log_file,
    level=LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# WEBHOOK HANDLERS
# ============================================================================

class WebhookSender:
    """Sends alerts via webhook to various services."""
    
    def __init__(self, webhook_url: str):
        """
        Initialize webhook sender.
        
        Args:
            webhook_url: Full webhook URL
        """
        self.webhook_url = webhook_url
        self.timeout = 10  # seconds
    
    def send_discord(self, status: str, message: str):
        """Send alert to Discord webhook."""
        payload = {
            "embeds": [
                {
                    "title": "Printer Status Alert",
                    "description": message,
                    "color": 16711680 if "OUT_OF_PAPER" in status else 65280,  # Red or Green
                    "fields": [
                        {
                            "name": "Status",
                            "value": status,
                            "inline": True
                        },
                        {
                            "name": "Timestamp",
                            "value": datetime.now().isoformat(),
                            "inline": True
                        }
                    ]
                }
            ]
        }
        return self._send_webhook(payload)
    
    def send_slack(self, status: str, message: str):
        """Send alert to Slack webhook."""
        color = "danger" if "OUT_OF_PAPER" in status else "good"
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": "Printer Status Alert",
                    "text": message,
                    "fields": [
                        {
                            "title": "Status",
                            "value": status,
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": datetime.now().isoformat(),
                            "short": True
                        }
                    ]
                }
            ]
        }
        return self._send_webhook(payload)
    
    def send_generic(self, status: str, message: str):
        """Send alert to generic HTTP webhook."""
        payload = {
            "event": "printer_status_change",
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        return self._send_webhook(payload)
    
    def _send_webhook(self, payload: dict) -> bool:
        """
        Send webhook request.
        
        Args:
            payload: JSON payload to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201, 204]:
                logger.info(f"Webhook sent successfully (HTTP {response.status_code})")
                return True
            else:
                logger.warning(f"Webhook failed with HTTP {response.status_code}")
                return False
                
        except requests.Timeout:
            logger.error(f"Webhook timeout after {self.timeout}s")
            return False
        except requests.ConnectionError:
            logger.error(f"Webhook connection error to {self.webhook_url}")
            return False
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return False

# ============================================================================
# PRINTER MONITOR POLLER
# ============================================================================

class PrinterMonitorPoller:
    """Polls printer monitor and sends alerts on status changes."""
    
    def __init__(self, printer_ip: str, printer_port: int, webhook_url: str):
        """
        Initialize poller.
        
        Args:
            printer_ip: Printer monitor IP
            printer_port: Printer monitor port
            webhook_url: Webhook URL for alerts
        """
        self.printer_ip = printer_ip
        self.printer_port = printer_port
        self.webhook_sender = WebhookSender(webhook_url)
        
        self.current_status = None
        self.last_status = None
        self.error_count = 0
        self.max_errors = 3
    
    def poll_status(self) -> Optional[str]:
        """
        Poll printer monitor for status.
        
        Returns:
            Status string or None if error
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.printer_ip, self.printer_port))
            sock.send(b"STATUS\r\n")
            response = sock.recv(1024).decode().strip()
            sock.close()
            
            self.error_count = 0  # Reset error count on success
            return response
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Poll error: {e}")
            if self.error_count >= self.max_errors:
                return "COMMUNICATION_ERROR"
            return None
    
    def on_status_change(self, new_status: str):
        """
        Handle status change and send webhook alert.
        
        Args:
            new_status: New paper status
        """
        logger.info(f"Status change: {self.last_status} → {new_status}")
        
        # Determine alert type and message
        if new_status == "OUT_OF_PAPER":
            message = "⚠️ ALERT: Printer paper has run out! Refill required immediately."
        elif new_status == "PAPER_OK":
            message = "✓ Printer paper refilled and operational."
        elif new_status == "SENSOR_ERROR":
            message = "🔴 ERROR: Printer sensor is not responding. Hardware check required."
        else:
            message = f"Printer status changed to: {new_status}"
        
        # Send webhook
        if WEBHOOK_ENABLED:
            self.webhook_sender.send_generic(new_status, message)
    
    def run(self):
        """Main polling loop."""
        logger.info("Printer Monitor webhook bridge started")
        
        while True:
            try:
                # Poll status
                status = self.poll_status()
                
                if status is None:
                    time.sleep(5)  # Retry sooner on error
                    continue
                
                # Check for status change
                self.current_status = status
                if self.current_status != self.last_status:
                    self.on_status_change(self.current_status)
                    self.last_status = self.current_status
                
                # Wait before next poll
                time.sleep(POLL_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Webhook bridge stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(POLL_INTERVAL)

# ============================================================================
# SETUP EXAMPLES
# ============================================================================

def setup_discord_webhook():
    """Example: Setup for Discord webhook."""
    print("""
    Discord Webhook Setup:
    
    1. In Discord server, create a webhook:
       Server Settings → Integrations → Webhooks → New Webhook
    
    2. Copy the webhook URL
    
    3. In this file, set:
       WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN"
       WEBHOOK_ENABLED = True
    
    4. Run the script as a systemd service
    """)

def setup_slack_webhook():
    """Example: Setup for Slack webhook."""
    print("""
    Slack Webhook Setup:
    
    1. Go to https://api.slack.com/apps
    
    2. Create new app from manifest or use existing
    
    3. Enable Incoming Webhooks
    
    4. Add new webhook to desired channel
    
    5. Copy the webhook URL
    
    6. In this file, set:
       WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
       WEBHOOK_ENABLED = True
    
    7. Run the script as a systemd service
    """)

# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    if not WEBHOOK_ENABLED:
        print("ERROR: WEBHOOK_ENABLED = False")
        print("Edit this file and set WEBHOOK_ENABLED = True")
        print("\nFor help setting up webhooks, see setup_discord_webhook() or setup_slack_webhook()")
        return
    
    if not WEBHOOK_URL or WEBHOOK_URL == "http://localhost:8000/webhook":
        print("ERROR: WEBHOOK_URL not configured")
        print("Edit this file and set WEBHOOK_URL to your actual webhook URL")
        return
    
    poller = PrinterMonitorPoller(PRINTER_IP, PRINTER_PORT, WEBHOOK_URL)
    poller.run()

if __name__ == "__main__":
    main()
