#!/usr/bin/env python3
"""
Simple Printer Paper Monitor - Telnet Server
Monitors GPIO sensor and responds to status queries via Telnet

Usage:
    python3 monitor.py
    
Connect via: telnet localhost 2323
Send: STATUS
Response: PAPER_OK or OUT_OF_PAPER
"""

import socket
import threading
import time
import sys

# ============================================================================
# CONFIGURATION
# ============================================================================

SENSOR_PIN = 17              # GPIO pin for paper sensor
TELNET_PORT = 2323           # Telnet port (non-privileged)
SENSOR_READ_INTERVAL = 0.5   # Check sensor every 0.5 seconds
DEBOUNCE_READS = 5           # Require 5 consistent reads
LOG_FILE = None              # Will be set to user home dir if needed

# Try to import GPIO library
try:
    from gpiozero import DigitalInputDevice
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False
    print("Warning: gpiozero not installed. Running in simulation mode.")

# ============================================================================
# SENSOR MANAGER
# ============================================================================

class SensorManager:
    """Simple sensor reader with debouncing."""
    
    def __init__(self):
        self.status = "INITIALIZING"
        self.sensor = None
        self.reading_count = 0
        self.last_reading = None
        
        # Initialize sensor
        if HAS_GPIO:
            try:
                self.sensor = DigitalInputDevice(SENSOR_PIN, pull_up=None)
                print(f"Sensor initialized on GPIO {SENSOR_PIN}")
            except Exception as e:
                print(f"Error initializing sensor: {e}")
                HAS_GPIO = False
    
    def get_status(self):
        """Get current sensor status."""
        try:
            # Read sensor (HIGH = reflection = paper out)
            if self.sensor:
                reading = self.sensor.value == 1
            else:
                # Simulation mode
                reading = False  # Assume paper OK
            
            # Debounce: need DEBOUNCE_READS consistent readings
            if reading == self.last_reading:
                self.reading_count += 1
            else:
                self.reading_count = 1
                self.last_reading = reading
            
            # Update status when stable
            if self.reading_count >= DEBOUNCE_READS:
                self.status = "OUT_OF_PAPER" if reading else "PAPER_OK"
            
            return self.status
        except Exception as e:
            print(f"Sensor error: {e}")
            return "SENSOR_ERROR"
    
    def cleanup(self):
        """Cleanup GPIO."""
        if self.sensor:
            self.sensor.close()


# ============================================================================
# TELNET SERVER
# ============================================================================

class TelnetServer:
    """Simple Telnet server for status queries."""
    
    def __init__(self, sensor):
        self.sensor = sensor
        self.running = True
        self.server = None
    
    def handle_client(self, client_socket, addr):
        """Handle individual client connection."""
        try:
            print(f"Client connected: {addr}")
            
            while self.running:
                data = client_socket.recv(1024).decode().strip()
                
                if not data:
                    break
                
                if data.upper() == "STATUS":
                    response = self.sensor.get_status() + "\n"
                    client_socket.send(response.encode())
                    print(f"Sent to {addr}: {response.strip()}")
                elif data.upper() == "QUIT":
                    break
                else:
                    client_socket.send(b"Unknown command\n")
        
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            client_socket.close()
            print(f"Client disconnected: {addr}")
    
    def start(self):
        """Start Telnet server."""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("0.0.0.0", TELNET_PORT))
        self.server.listen(5)
        print(f"Telnet server listening on port {TELNET_PORT}")
        
        try:
            while self.running:
                client_socket, addr = self.server.accept()
                thread = threading.Thread(target=self.handle_client, 
                                        args=(client_socket, addr))
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.stop()
    
    def stop(self):
        """Stop server."""
        self.running = False
        if self.server:
            self.server.close()


# ============================================================================
# SENSOR POLLING LOOP
# ============================================================================

def poll_sensor(sensor):
    """Continuously poll sensor in background."""
    while True:
        sensor.get_status()
        time.sleep(SENSOR_READ_INTERVAL)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    sensor = SensorManager()
    
    # Start sensor polling thread
    poll_thread = threading.Thread(target=poll_sensor, args=(sensor,), daemon=True)
    poll_thread.start()
    
    # Start Telnet server
    server = TelnetServer(sensor)
    
    try:
        server.start()
    except KeyboardInterrupt:
        pass
    finally:
        sensor.cleanup()
        print("Cleanup complete")
        sys.exit(0)
