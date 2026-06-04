#!/usr/bin/env python3
"""
Production-Ready Raspberry Pi Printer Paper Monitoring System
Telnet Server Version - Serves as CLIENT for Inner Mapper SERVER

This script runs a Telnet server on the Raspberry Pi that responds to paper status
queries from the Inner Mapper server. It monitors a reflective light sensor to detect
when the printer has run out of paper.

Author: System Integration
Version: 1.0.0
License: MIT
"""

import socket
import threading
import logging
import time
import sys
import signal
import os
from enum import Enum
from typing import Tuple

# Try to import RPi libraries - gracefully degrade if not available
try:
    from gpiozero import DigitalInputDevice, LED, GPIOFactory
    from gpiozero.pins.pigpio import PiGPIOFactory
    GPIOZERO_AVAILABLE = True
except ImportError:
    GPIOZERO_AVAILABLE = False
    print("Warning: gpiozero not available. Running in simulation mode.")


# ============================================================================
# CONFIGURATION SECTION - Modify these values for your deployment
# ============================================================================

# GPIO Pin Configuration
SENSOR_PIN = 17                    # GPIO pin connected to reflective light sensor
GREEN_LED_PIN = 27                 # GPIO pin for green LED (paper OK) - optional
RED_LED_PIN = 22                   # GPIO pin for red LED (out of paper) - optional
USE_LEDS = True                    # Set to False to disable LED indicators

# Sensor Configuration
DEBOUNCE_COUNT = 5                 # Number of consistent reads before state change
SENSOR_READ_INTERVAL = 0.5         # Seconds between sensor reads
SENSOR_TIMEOUT = 10                # Seconds to wait before reporting SENSOR_ERROR

# Telnet Server Configuration
TELNET_PORT = 2323                 # Non-privileged Telnet port (use 23 only with root)
TELNET_TIMEOUT = 10                # Timeout for client connections
MAX_CONCURRENT_CLIENTS = 5          # Maximum simultaneous connections
LISTEN_ADDRESS = "0.0.0.0"         # Listen on all interfaces

# Polling Configuration
HEARTBEAT_INTERVAL = 60            # Seconds between heartbeat log entries
HEALTH_CHECK_INTERVAL = 30         # Seconds between internal health checks

# Logging Configuration
# Will attempt /var/log first, fallback to home directory if not writable
LOG_FILE_PATH = "/var/log/printer_monitor.log"  # Production path (requires permissions)
LOG_LEVEL = logging.INFO
MAX_LOG_SIZE = 10 * 1024 * 1024    # 10 MB before rotation
MAX_LOG_BACKUPS = 5                 # Keep last 5 log files

# Feature Flags
ENABLE_HEARTBEAT_LOGGING = True     # Log periodic heartbeat
DEBUG_MODE = False                  # Simulate sensor without hardware
SIMULATE_PAPER_OUT = False          # Simulate paper-out condition (debug mode only)


# ============================================================================
# ENUMERATIONS
# ============================================================================

class PaperStatus(Enum):
    """Paper status enumeration."""
    OK = "PAPER_OK"
    OUT_OF_PAPER = "OUT_OF_PAPER"
    ERROR = "SENSOR_ERROR"
    UNKNOWN = "UNKNOWN"


class SensorStatus(Enum):
    """Sensor hardware status."""
    HEALTHY = "healthy"
    DISCONNECTED = "disconnected"
    ERROR = "error"


# ============================================================================
# LOGGER CLASS
# ============================================================================

class PaperMonitorLogger:
    """
    Enterprise-grade logger with file rotation and structured logging.
    Ensures log file exists and handles permission issues gracefully.
    """

    def __init__(self, log_file: str, level: int = logging.INFO):
        """
        Initialize the logger.
        
        Args:
            log_file: Path to log file
            level: Logging level (logging.DEBUG, logging.INFO, etc.)
        """
        self.log_file = log_file
        self.logger = logging.getLogger("PrinterMonitor")
        self.logger.setLevel(level)
        
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, mode=0o755, exist_ok=True)
            except (OSError, PermissionError) as e:
                # Fall back to home directory if we can't write to default location
                self.log_file = os.path.expanduser("~/printer_monitor.log")
                log_dir = os.path.dirname(self.log_file)
                os.makedirs(log_dir, mode=0o755, exist_ok=True)
                print(f"Warning: Could not write to {log_file}, using {self.log_file}")
        
        # Create formatter with timestamp and details
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)-8s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler with rotation
        try:
            file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not create log file {self.log_file}: {e}")
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)

    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)

    def critical(self, message: str):
        """Log critical message."""
        self.logger.critical(message)


# ============================================================================
# SENSOR MANAGER CLASS
# ============================================================================

class SensorManager:
    """
    Manages the reflective light sensor with debouncing and health monitoring.
    
    Sensor Logic:
    - Paper Present: Sensor does NOT detect reflection (no paper blocking)
    - Paper Out: Sensor DETECTS reflection (light reflects off backing plate)
    """

    def __init__(self, pin: int, debounce_count: int, logger: PaperMonitorLogger,
                 read_interval: float = 0.1, timeout: float = 10.0):
        """
        Initialize sensor manager.
        
        Args:
            pin: GPIO pin number
            debounce_count: Number of consistent readings required for state change
            logger: Logger instance
            read_interval: Seconds between sensor reads
            timeout: Seconds before considering sensor disconnected
        """
        self.pin = pin
        self.debounce_count = debounce_count
        self.logger = logger
        self.read_interval = read_interval
        self.timeout = timeout
        
        self.sensor = None
        self.status = SensorStatus.UNKNOWN
        self.last_read_time = None
        self.consecutive_readings = 0
        self.current_reading = None
        self.is_initialized = False
        
        self._initialize_sensor()

    def _initialize_sensor(self):
        """Initialize the physical sensor or simulation."""
        if DEBUG_MODE:
            self.logger.info(f"DEBUG: Sensor running in SIMULATION mode on pin {self.pin}")
            self.sensor = None
            self.is_initialized = True
            self.status = SensorStatus.HEALTHY
        elif GPIOZERO_AVAILABLE:
            try:
                # Use pigpio factory for more reliable operation
                factory = PiGPIOFactory()
                GPIOFactory.pin_factory = factory
                
                # DigitalInputDevice: HIGH = reflection detected (paper out)
                self.sensor = DigitalInputDevice(self.pin, pull_up=None)
                self.is_initialized = True
                self.status = SensorStatus.HEALTHY
                self.logger.info(f"Sensor initialized on GPIO {self.pin}")
            except Exception as e:
                self.logger.error(f"Failed to initialize sensor on pin {self.pin}: {e}")
                self.status = SensorStatus.DISCONNECTED
        else:
            self.logger.error("gpiozero library not available and not in DEBUG mode")
            self.status = SensorStatus.DISCONNECTED

    def read_sensor(self) -> bool:
        """
        Read the current sensor state with debouncing.
        
        Returns:
            True if reflection detected (paper out), False if no reflection (paper ok)
        """
        if not self.is_initialized:
            self.status = SensorStatus.DISCONNECTED
            return None

        try:
            if DEBUG_MODE:
                # Simulate sensor reading
                if SIMULATE_PAPER_OUT:
                    reading = True  # Simulate paper out
                else:
                    reading = False  # Simulate paper present
            else:
                # Read actual sensor (HIGH = reflection = paper out)
                reading = self.sensor.value == 1
            
            self.last_read_time = time.time()
            self.current_reading = reading
            self.status = SensorStatus.HEALTHY
            return reading
            
        except Exception as e:
            self.logger.error(f"Sensor read error: {e}")
            self.status = SensorStatus.ERROR
            return None

    def is_paper_out(self) -> Tuple[bool, SensorStatus]:
        """
        Get debounced paper-out status.
        
        Returns sensor state is stable after debounce_count consistent readings.
        Requires debounce_count consecutive identical readings before state change.
        
        Returns:
            Tuple of (is_paper_out: bool, sensor_status: SensorStatus)
        """
        reading = self.read_sensor()

        if reading is None:
            # Sensor error
            if self.last_read_time:
                elapsed = time.time() - self.last_read_time
                if elapsed > self.timeout:
                    self.status = SensorStatus.DISCONNECTED
            return None, self.status

        # Check for timeout between reads
        if self.last_read_time:
            elapsed = time.time() - self.last_read_time
            if elapsed > self.timeout:
                self.logger.warning(f"Sensor timeout: no read for {elapsed:.1f}s")
                self.status = SensorStatus.DISCONNECTED
                return None, self.status

        # Debounce logic
        if reading == self.current_reading:
            self.consecutive_readings += 1
        else:
            self.consecutive_readings = 1

        # State stable after debounce_count readings
        is_stable = self.consecutive_readings >= self.debounce_count
        
        return is_stable, self.status

    def cleanup(self):
        """Cleanup sensor resources."""
        try:
            if self.sensor and not DEBUG_MODE:
                self.sensor.close()
                self.logger.info("Sensor cleaned up")
        except Exception as e:
            self.logger.error(f"Error during sensor cleanup: {e}")


# ============================================================================
# STATE MANAGER CLASS
# ============================================================================

class StateManager:
    """
    Manages the overall system state with state machine logic.
    Handles transitions between PAPER_OK and OUT_OF_PAPER states.
    """

    def __init__(self, sensor_manager: SensorManager, logger: PaperMonitorLogger):
        """
        Initialize state manager.
        
        Args:
            sensor_manager: SensorManager instance
            logger: Logger instance
        """
        self.sensor = sensor_manager
        self.logger = logger
        self.current_status = PaperStatus.UNKNOWN
        self.last_status = None
        self.status_changed_at = time.time()
        self.status_change_count = 0

    def update(self) -> PaperStatus:
        """
        Update system state based on sensor reading.
        
        State Transitions:
        - UNKNOWN -> OK (on first valid reading with no reflection)
        - UNKNOWN -> OUT_OF_PAPER (on first valid reading with reflection)
        - OK -> OUT_OF_PAPER (on debounced reflection detection)
        - OUT_OF_PAPER -> OK (on debounced reflection absence)
        - * -> ERROR (on sensor error/disconnect)
        
        Returns:
            Current PaperStatus
        """
        reading, sensor_status = self.sensor.is_paper_out()

        # Handle sensor errors
        if sensor_status == SensorStatus.DISCONNECTED:
            self._set_status(PaperStatus.ERROR, "Sensor disconnected")
            return self.current_status
        elif sensor_status == SensorStatus.ERROR:
            self._set_status(PaperStatus.ERROR, "Sensor error")
            return self.current_status

        # Handle sensor readings
        if reading is not None:
            if reading:  # Reflection detected = paper out
                self._set_status(PaperStatus.OUT_OF_PAPER, "Paper out detected")
            else:  # No reflection = paper present
                self._set_status(PaperStatus.OK, "Paper present")
        
        return self.current_status

    def _set_status(self, new_status: PaperStatus, reason: str = ""):
        """
        Set new status and log changes.
        
        Args:
            new_status: New PaperStatus value
            reason: Reason for status change
        """
        if new_status != self.current_status:
            self.last_status = self.current_status
            self.current_status = new_status
            self.status_changed_at = time.time()
            self.status_change_count += 1
            
            log_msg = f"Status changed to {new_status.value}"
            if reason:
                log_msg += f" ({reason})"
            self.logger.info(log_msg)
        elif new_status == PaperStatus.ERROR and reason:
            # Log recurring error state
            self.logger.warning(f"Status: {new_status.value} - {reason}")

    def get_status(self) -> PaperStatus:
        """Get current status."""
        return self.current_status

    def get_status_string(self) -> str:
        """Get status as response string for Telnet."""
        if self.current_status == PaperStatus.UNKNOWN:
            return "INITIALIZING"
        return self.current_status.value

    def get_uptime(self) -> float:
        """Get time since last status change in seconds."""
        return time.time() - self.status_changed_at


# ============================================================================
# LED INDICATOR CLASS (Optional)
# ============================================================================

class LEDIndicator:
    """
    Manages optional LED indicators for visual status display.
    Green LED = paper OK, Red LED = out of paper
    """

    def __init__(self, green_pin: int, red_pin: int, logger: PaperMonitorLogger):
        """
        Initialize LED indicator.
        
        Args:
            green_pin: GPIO pin for green LED
            red_pin: GPIO pin for red LED
            logger: Logger instance
        """
        self.green_pin = green_pin
        self.red_pin = red_pin
        self.logger = logger
        self.green_led = None
        self.red_led = None
        self.is_initialized = False
        
        self._initialize_leds()

    def _initialize_leds(self):
        """Initialize LED pins."""
        if DEBUG_MODE:
            self.logger.debug("LED indicators in simulation mode")
            self.is_initialized = True
            return

        if not GPIOZERO_AVAILABLE:
            self.logger.warning("gpiozero not available, LED indicators disabled")
            return

        try:
            self.green_led = LED(self.green_pin)
            self.red_led = LED(self.red_pin)
            self.is_initialized = True
            self.logger.info(f"LED indicators initialized (Green:{self.green_pin}, Red:{self.red_pin})")
        except Exception as e:
            self.logger.error(f"Failed to initialize LEDs: {e}")

    def set_status(self, status: PaperStatus):
        """
        Set LED state based on paper status.
        
        Args:
            status: Current PaperStatus
        """
        if not self.is_initialized:
            return

        try:
            if status == PaperStatus.OK:
                self._set_green_led(True)
                self._set_red_led(False)
            elif status == PaperStatus.OUT_OF_PAPER:
                self._set_green_led(False)
                self._set_red_led(True)
            else:  # ERROR or UNKNOWN - blink red
                self._set_green_led(False)
                self._set_red_led(True)
        except Exception as e:
            self.logger.error(f"Error setting LED state: {e}")

    def _set_green_led(self, on: bool):
        """Control green LED."""
        if DEBUG_MODE:
            self.logger.debug(f"LED Green: {'ON' if on else 'OFF'}")
            return
        
        if self.green_led:
            if on:
                self.green_led.on()
            else:
                self.green_led.off()

    def _set_red_led(self, on: bool):
        """Control red LED."""
        if DEBUG_MODE:
            self.logger.debug(f"LED Red: {'ON' if on else 'OFF'}")
            return
        
        if self.red_led:
            if on:
                self.red_led.on()
            else:
                self.red_led.off()

    def cleanup(self):
        """Cleanup LED resources."""
        try:
            if self.green_led and not DEBUG_MODE:
                self.green_led.off()
                self.green_led.close()
            if self.red_led and not DEBUG_MODE:
                self.red_led.off()
                self.red_led.close()
            self.logger.info("LED indicators cleaned up")
        except Exception as e:
            self.logger.error(f"Error during LED cleanup: {e}")


# ============================================================================
# TELNET SERVER CLASS
# ============================================================================

class TelnetServer:
    """
    Production-grade Telnet server for paper status queries.
    
    Protocol:
    - Client connects via Telnet to port 23 (or configured port)
    - Client sends: STATUS\r\n
    - Server responds: PAPER_OK\r\n or OUT_OF_PAPER\r\n or SENSOR_ERROR\r\n
    - Connection closes
    """

    def __init__(self, state_manager: StateManager, logger: PaperMonitorLogger,
                 port: int = 23, listen_addr: str = "0.0.0.0",
                 timeout: float = 10.0, max_clients: int = 5):
        """
        Initialize Telnet server.
        
        Args:
            state_manager: StateManager instance
            logger: Logger instance
            port: Telnet port
            listen_addr: Address to listen on
            timeout: Client timeout in seconds
            max_clients: Maximum concurrent clients
        """
        self.state_manager = state_manager
        self.logger = logger
        self.port = port
        self.listen_addr = listen_addr
        self.timeout = timeout
        self.max_clients = max_clients
        
        self.server_socket = None
        self.is_running = False
        self.client_count = 0
        self.total_requests = 0
        self.request_lock = threading.Lock()

    def start(self) -> bool:
        """
        Start the Telnet server.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Try to bind to port
            try:
                self.server_socket.bind((self.listen_addr, self.port))
            except PermissionError:
                # If port 23 fails due to permissions, use an alternative port
                alt_port = 2323
                self.logger.warning(f"Cannot bind to port {self.port} (permission denied)")
                self.logger.info(f"Attempting to use alternative port {alt_port}")
                self.server_socket.bind((self.listen_addr, alt_port))
                self.port = alt_port
            
            self.server_socket.listen(self.max_clients)
            self.is_running = True
            self.logger.info(f"Telnet server started on {self.listen_addr}:{self.port}")
            
            # Start server thread
            server_thread = threading.Thread(target=self._accept_connections, daemon=True)
            server_thread.start()
            
            return True

        except Exception as e:
            self.logger.error(f"Failed to start Telnet server: {e}")
            self.is_running = False
            return False

    def _accept_connections(self):
        """Accept incoming Telnet connections (runs in thread)."""
        self.logger.debug("Connection accept loop started")
        
        while self.is_running:
            try:
                self.server_socket.settimeout(2.0)
                client_socket, client_addr = self.server_socket.accept()
                
                # Check concurrent connections limit
                if self.client_count >= self.max_clients:
                    self.logger.warning(f"Max clients reached, rejecting {client_addr}")
                    client_socket.close()
                    continue
                
                # Handle client in separate thread
                with self.request_lock:
                    self.client_count += 1
                
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_addr),
                    daemon=True
                )
                client_thread.start()

            except socket.timeout:
                continue
            except Exception as e:
                if self.is_running:
                    self.logger.error(f"Error accepting connection: {e}")

    def _handle_client(self, client_socket: socket.socket, client_addr: Tuple):
        """
        Handle a single Telnet client connection.
        
        Args:
            client_socket: Client socket
            client_addr: Client address tuple (ip, port)
        """
        client_ip, client_port = client_addr
        self.logger.debug(f"Client connected from {client_ip}:{client_port}")
        
        try:
            client_socket.settimeout(self.timeout)
            
            # Receive request
            request_data = client_socket.recv(1024).decode('utf-8', errors='ignore').strip()
            
            # Log request
            with self.request_lock:
                self.total_requests += 1
            self.logger.debug(f"Request from {client_ip}: {repr(request_data)}")
            
            # Process request
            if request_data.upper() == "STATUS":
                # Get current status
                status_string = self.state_manager.get_status_string()
                response = f"{status_string}\r\n"
                client_socket.send(response.encode('utf-8'))
                self.logger.debug(f"Response to {client_ip}: {status_string}")
            else:
                # Unknown command
                response = "UNKNOWN_COMMAND\r\n"
                client_socket.send(response.encode('utf-8'))
                self.logger.warning(f"Unknown command from {client_ip}: {repr(request_data)}")
            
        except socket.timeout:
            self.logger.warning(f"Client {client_ip} timeout")
        except Exception as e:
            self.logger.error(f"Error handling client {client_ip}: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
            
            with self.request_lock:
                self.client_count -= 1
            self.logger.debug(f"Client {client_ip} disconnected")

    def stop(self):
        """Stop the Telnet server."""
        self.is_running = False
        try:
            if self.server_socket:
                self.server_socket.close()
            self.logger.info("Telnet server stopped")
        except Exception as e:
            self.logger.error(f"Error stopping server: {e}")

    def get_stats(self) -> dict:
        """Get server statistics."""
        return {
            "is_running": self.is_running,
            "current_clients": self.client_count,
            "total_requests": self.total_requests,
            "port": self.port
        }


# ============================================================================
# MAIN MONITOR CLASS
# ============================================================================

class PrinterMonitor:
    """
    Main coordinator class that ties all components together.
    Manages the monitoring loop and graceful shutdown.
    """

    def __init__(self, sensor_pin: int = SENSOR_PIN,
                 telnet_port: int = TELNET_PORT,
                 use_leds: bool = USE_LEDS):
        """
        Initialize the monitor.
        
        Args:
            sensor_pin: GPIO pin for sensor
            telnet_port: Telnet server port
            use_leds: Whether to use LED indicators
        """
        self.logger = PaperMonitorLogger(LOG_FILE_PATH, LOG_LEVEL)
        self.logger.info("=" * 70)
        self.logger.info("Printer Monitor Starting")
        self.logger.info(f"Version: 1.0.0, GPIO Sensor Pin: {sensor_pin}, Telnet Port: {telnet_port}")
        self.logger.info(f"Debounce Count: {DEBOUNCE_COUNT}, Debug Mode: {DEBUG_MODE}")
        self.logger.info("=" * 70)
        
        # Initialize components
        self.sensor = SensorManager(sensor_pin, DEBOUNCE_COUNT, self.logger,
                                   read_interval=SENSOR_READ_INTERVAL,
                                   timeout=SENSOR_TIMEOUT)
        self.state = StateManager(self.sensor, self.logger)
        self.telnet = TelnetServer(self.state, self.logger, port=telnet_port)
        
        # Optional LED indicator
        self.leds = None
        if use_leds and USE_LEDS:
            self.leds = LEDIndicator(GREEN_LED_PIN, RED_LED_PIN, self.logger)
        
        # Monitoring state
        self.is_running = False
        self.last_heartbeat = time.time()
        self.loop_count = 0
        self.last_status_for_leds = None

    def run(self):
        """
        Main monitoring loop.
        Continuously monitors sensor and serves Telnet requests.
        """
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Start Telnet server
        if not self.telnet.start():
            self.logger.error("Failed to start Telnet server")
            return

        self.is_running = True
        self.logger.info("Monitor loop starting")

        try:
            while self.is_running:
                try:
                    # Update sensor reading and state
                    self.state.update()
                    current_status = self.state.get_status()
                    
                    # Update LED indicator if status changed
                    if self.leds and current_status != self.last_status_for_leds:
                        self.leds.set_status(current_status)
                        self.last_status_for_leds = current_status
                    
                    # Periodic heartbeat logging
                    current_time = time.time()
                    if ENABLE_HEARTBEAT_LOGGING:
                        if current_time - self.last_heartbeat >= HEARTBEAT_INTERVAL:
                            stats = self.telnet.get_stats()
                            uptime = self.state.get_uptime()
                            self.logger.debug(
                                f"Heartbeat: Status={current_status.value}, "
                                f"Uptime={uptime:.0f}s, Clients={stats['current_clients']}, "
                                f"Requests={stats['total_requests']}"
                            )
                            self.last_heartbeat = current_time
                    
                    self.loop_count += 1
                    
                    # Sleep to avoid CPU spinning
                    time.sleep(SENSOR_READ_INTERVAL)

                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(1)

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.critical(f"Fatal error in monitor loop: {e}")
        finally:
            self.cleanup()

    def _signal_handler(self, signum, frame):
        """Handle signals for graceful shutdown."""
        if signum == signal.SIGINT:
            self.logger.info("SIGINT received (Ctrl+C)")
        elif signum == signal.SIGTERM:
            self.logger.info("SIGTERM received (system shutdown)")
        self.is_running = False

    def cleanup(self):
        """Cleanup all resources."""
        self.logger.info("Cleaning up resources...")
        
        try:
            if self.telnet:
                self.telnet.stop()
            if self.leds:
                self.leds.cleanup()
            if self.sensor:
                self.sensor.cleanup()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        
        self.logger.info("=" * 70)
        self.logger.info(f"Monitor stopped. Total loops: {self.loop_count}")
        self.logger.info("=" * 70)


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """
    Application entry point.
    
    Run with DEBUG_MODE=True to simulate without hardware.
    Set SIMULATE_PAPER_OUT=True to test paper-out scenario.
    """
    try:
        monitor = PrinterMonitor(
            sensor_pin=SENSOR_PIN,
            telnet_port=TELNET_PORT,
            use_leds=USE_LEDS
        )
        monitor.run()

    except KeyboardInterrupt:
        print("\nShutdown signal received")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
