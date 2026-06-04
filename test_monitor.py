#!/usr/bin/env python3
"""
Printer Monitor Test and Debug Script
Provides utilities for testing printer monitor functionality without running the full service

Usage:
    python3 test_monitor.py --help
    python3 test_monitor.py --telnet-test
    python3 test_monitor.py --stress-test
    python3 test_monitor.py --gpio-test
"""

import socket
import sys
import argparse
import time
import subprocess
from typing import Tuple

# ============================================================================
# COLORS FOR TERMINAL OUTPUT
# ============================================================================

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{msg:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")

# ============================================================================
# TELNET TESTS
# ============================================================================

def test_telnet_connection(ip: str, port: int, timeout: int = 5) -> Tuple[bool, str]:
    """
    Test Telnet connection to printer monitor.
    
    Args:
        ip: Printer monitor IP address
        port: Telnet port
        timeout: Connection timeout in seconds
        
    Returns:
        Tuple of (success: bool, response: str)
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        sock.send(b"STATUS\r\n")
        response = sock.recv(1024).decode().strip()
        sock.close()
        return True, response
    except socket.timeout:
        return False, f"Timeout after {timeout}s"
    except ConnectionRefusedError:
        return False, "Connection refused (service not running?)"
    except Exception as e:
        return False, str(e)

def telnet_test(args):
    """Test Telnet connectivity."""
    print_header("TELNET CONNECTIVITY TEST")
    
    ip = args.ip
    port = args.port
    
    print_info(f"Testing connection to {ip}:{port}...")
    
    success, response = test_telnet_connection(ip, port, timeout=5)
    
    if success:
        print_success(f"Connected successfully")
        print(f"  Response: {response}")
        
        if response in ["PAPER_OK", "OUT_OF_PAPER", "SENSOR_ERROR"]:
            print_success(f"Valid status response: {response}")
        else:
            print_warning(f"Unexpected response: {response}")
    else:
        print_error(f"Connection failed: {response}")
        print_info("Troubleshooting steps:")
        print("  1. Verify Raspberry Pi is reachable: ping " + ip)
        print("  2. Check service is running: sudo systemctl status printer_monitor")
        print("  3. Verify port number: sudo netstat -tlnp | grep python3")
        print("  4. Check firewall: sudo ufw allow " + str(port))
        return False
    
    return True

# ============================================================================
# POLLING TESTS
# ============================================================================

def polling_test(args):
    """Test repeated polling with statistics."""
    print_header("POLLING TEST")
    
    ip = args.ip
    port = args.port
    count = args.count
    interval = args.interval
    
    print_info(f"Polling {ip}:{port} {count} times with {interval}s interval...")
    
    responses = {}
    failures = 0
    total_time = 0
    
    for i in range(count):
        start = time.time()
        success, response = test_telnet_connection(ip, port, timeout=5)
        elapsed = time.time() - start
        total_time += elapsed
        
        status = "✓" if success else "✗"
        print(f"  {i+1:3d}. {status} {response:20s} ({elapsed:.3f}s)")
        
        if success:
            responses[response] = responses.get(response, 0) + 1
        else:
            failures += 1
        
        if i < count - 1:
            time.sleep(interval)
    
    # Statistics
    print_info(f"\nPolling Statistics:")
    print(f"  Total polls: {count}")
    print(f"  Successful: {count - failures}")
    print(f"  Failed: {failures}")
    print(f"  Success rate: {((count - failures) / count * 100):.1f}%")
    print(f"  Average response time: {(total_time / count):.3f}s")
    
    if responses:
        print(f"  Status distribution:")
        for status, cnt in responses.items():
            print(f"    {status}: {cnt}")
    
    return failures == 0

# ============================================================================
# STRESS TESTS
# ============================================================================

def stress_test(args):
    """Stress test with rapid connections."""
    print_header("STRESS TEST")
    
    ip = args.ip
    port = args.port
    duration = args.duration
    
    print_info(f"Stress testing {ip}:{port} for {duration} seconds...")
    
    start_time = time.time()
    attempts = 0
    successes = 0
    failures_list = []
    
    while time.time() - start_time < duration:
        success, response = test_telnet_connection(ip, port, timeout=2)
        attempts += 1
        
        if success:
            successes += 1
        else:
            failures_list.append(response)
        
        # Print progress every 10 attempts
        if attempts % 10 == 0:
            elapsed = time.time() - start_time
            rate = attempts / elapsed
            print(f"  {attempts:4d} attempts in {elapsed:.1f}s ({rate:.1f} req/s)")
    
    # Results
    elapsed_time = time.time() - start_time
    success_rate = (successes / attempts * 100) if attempts > 0 else 0
    
    print_info(f"\nStress Test Results:")
    print(f"  Duration: {elapsed_time:.1f}s")
    print(f"  Total attempts: {attempts}")
    print(f"  Successful: {successes}")
    print(f"  Failed: {attempts - successes}")
    print(f"  Success rate: {success_rate:.1f}%")
    print(f"  Requests per second: {(attempts / elapsed_time):.1f}")
    
    if failures_list and len(set(failures_list)) > 0:
        print_info(f"  Failure types:")
        for error in set(failures_list):
            count = failures_list.count(error)
            print(f"    {error}: {count}")
    
    return success_rate >= 95

# ============================================================================
# GPIO TESTS
# ============================================================================

def gpio_test(args):
    """Test GPIO functionality."""
    print_header("GPIO FUNCTIONALITY TEST")
    
    try:
        from gpiozero import DigitalInputDevice, LED, GPIOFactory
        from gpiozero.pins.pigpio import PiGPIOFactory
    except ImportError:
        print_error("gpiozero not installed. Run: sudo pip3 install gpiozero pigpio")
        return False
    
    # Check pigpio
    print_info("Checking pigpio daemon...")
    try:
        result = subprocess.run(['pigs', 'hwver'], capture_output=True, timeout=2)
        if result.returncode == 0:
            print_success("pigpio daemon is running")
        else:
            print_warning("pigpio may not be running properly")
    except FileNotFoundError:
        print_warning("pigpio tools not found")
    except Exception as e:
        print_warning(f"pigpio check error: {e}")
    
    # Test sensor input (GPIO 17)
    print_info("\nTesting sensor input (GPIO 17)...")
    try:
        factory = PiGPIOFactory()
        GPIOFactory.pin_factory = factory
        
        sensor = DigitalInputDevice(17)
        readings = []
        for i in range(5):
            readings.append(sensor.value)
            time.sleep(0.1)
        
        sensor.close()
        
        print_success(f"Sensor readings: {readings}")
        if len(set(readings)) > 1:
            print_success("Sensor is responsive to changes")
        else:
            print_warning("Sensor always reads the same value")
    except Exception as e:
        print_error(f"Sensor test failed: {e}")
        return False
    
    # Test green LED (GPIO 27)
    print_info("\nTesting green LED (GPIO 27)...")
    try:
        led_green = LED(27)
        led_green.on()
        print_info("LED should be ON now")
        time.sleep(1)
        led_green.off()
        print_info("LED should be OFF now")
        led_green.close()
        print_success("Green LED test passed")
    except Exception as e:
        print_warning(f"Green LED test failed: {e}")
    
    # Test red LED (GPIO 22)
    print_info("\nTesting red LED (GPIO 22)...")
    try:
        led_red = LED(22)
        led_red.on()
        print_info("LED should be ON now")
        time.sleep(1)
        led_red.off()
        print_info("LED should be OFF now")
        led_red.close()
        print_success("Red LED test passed")
    except Exception as e:
        print_warning(f"Red LED test failed: {e}")
    
    return True

# ============================================================================
# SYSTEM DIAGNOSTICS
# ============================================================================

def system_test(args):
    """Run system diagnostics."""
    print_header("SYSTEM DIAGNOSTICS")
    
    # Python version
    print_info("Python version:")
    print(f"  {sys.version}")
    
    # Check gpiozero
    print_info("\nChecking Python packages:")
    try:
        import gpiozero
        print_success(f"  gpiozero: {gpiozero.__version__}")
    except ImportError:
        print_error("  gpiozero: NOT INSTALLED")
    
    try:
        import requests
        print_success(f"  requests: {requests.__version__}")
    except ImportError:
        print_warning("  requests: NOT INSTALLED (optional)")
    
    # Service status
    print_info("\nService status:")
    try:
        result = subprocess.run(
            ['sudo', 'systemctl', 'status', 'printer_monitor', '--no-pager'],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print_success("Service is running")
        else:
            print_warning("Service is not running")
    except Exception as e:
        print_warning(f"Could not check service status: {e}")
    
    # Network connectivity
    print_info("\nNetwork connectivity:")
    try:
        sock = socket.create_connection(("8.8.8.8", 53), timeout=2)
        sock.close()
        print_success("Internet connectivity OK")
    except Exception as e:
        print_warning(f"Internet connectivity issue: {e}")
    
    return True

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Printer Monitor Test and Debug Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_monitor.py --telnet-test
  python3 test_monitor.py --polling-test --count 10
  python3 test_monitor.py --stress-test --duration 30
  python3 test_monitor.py --gpio-test
  python3 test_monitor.py --system-test
  python3 test_monitor.py --all
        """
    )
    
    # Global options
    parser.add_argument('--ip', default='localhost', help='Printer monitor IP (default: localhost)')
    parser.add_argument('--port', type=int, default=2323, help='Telnet port (default: 2323)')
    
    # Test types
    parser.add_argument('--telnet-test', action='store_true', help='Test Telnet connectivity')
    parser.add_argument('--polling-test', action='store_true', help='Test repeated polling')
    parser.add_argument('--count', type=int, default=10, help='Number of polls for polling test')
    parser.add_argument('--interval', type=float, default=1.0, help='Interval between polls (seconds)')
    
    parser.add_argument('--stress-test', action='store_true', help='Stress test with rapid connections')
    parser.add_argument('--duration', type=int, default=10, help='Stress test duration (seconds)')
    
    parser.add_argument('--gpio-test', action='store_true', help='Test GPIO functionality')
    parser.add_argument('--system-test', action='store_true', help='System diagnostics')
    
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    # If no tests specified, show help
    if not any([args.telnet_test, args.polling_test, args.stress_test, 
                args.gpio_test, args.system_test, args.all]):
        parser.print_help()
        return 0
    
    results = {}
    
    # Run tests
    if args.telnet_test or args.all:
        results['Telnet'] = telnet_test(args)
    
    if args.polling_test or args.all:
        results['Polling'] = polling_test(args)
    
    if args.stress_test or args.all:
        results['Stress'] = stress_test(args)
    
    if args.gpio_test or args.all:
        results['GPIO'] = gpio_test(args)
    
    if args.system_test or args.all:
        results['System'] = system_test(args)
    
    # Summary
    if results:
        print_header("TEST SUMMARY")
        for name, result in results.items():
            status = "PASS" if result else "FAIL"
            color = Colors.GREEN if result else Colors.RED
            print(f"{color}{name:20s}: {status}{Colors.RESET}")
        
        # Overall result
        all_passed = all(results.values())
        print()
        if all_passed:
            print_success("All tests passed!")
            return 0
        else:
            print_error("Some tests failed")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
