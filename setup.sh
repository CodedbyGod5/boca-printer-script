#!/bin/bash
# Setup Script for Printer Monitor on Debian GNU/Linux
# Compatible with Debian 13 (Trixie) and other systemd-based distributions

set -e  # Exit on error

echo "╔══════════════════════════════════════════════╗"
echo "║  Printer Monitor Setup for Debian GNU/Linux  ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "System Information:"
echo "  OS: $(lsb_release -d 2>/dev/null | cut -f2 || echo 'Linux')"
echo "  Kernel: $(uname -r)"
echo "  User: $(whoami)"
echo ""

# Detect if on Raspberry Pi
if grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "✓ Detected Raspberry Pi: $(cat /proc/device-tree/model)"
    PI_MODE=true
else
    echo "ℹ Not a Raspberry Pi - will use simulation mode if GPIO hardware unavailable"
    PI_MODE=false
fi
echo ""

# Check Python version
echo "📋 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Installing..."
    sudo apt update
    sudo apt install -y python3
else
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "✓ Python 3 version: $PYTHON_VERSION"
fi
echo ""

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y python3-pip

if [ "$PI_MODE" = true ]; then
    echo "Installing Raspberry Pi GPIO support..."
    sudo apt install -y python3-gpiozero
fi
echo ""

# Install Python packages
echo "📥 Installing Python packages from requirements.txt..."
pip3 install --user -r requirements.txt
echo ""

# Create log directory with appropriate permissions
echo "🔧 Setting up logging..."
if [ -w /var/log ]; then
    echo "✓ /var/log is writable"
    echo "✓ Log files will be saved to /var/log/printer_monitor.log"
else
    echo "ℹ /var/log requires elevated permissions"
    echo "✓ Log files will be saved to $HOME/printer_monitor.log"
fi
echo ""

# Verify installation
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo ""
echo "1. Test the monitor in simulation mode:"
echo "   python3 printer_monitor.py"
echo ""
echo "2. Connect via Telnet:"
echo "   telnet localhost 2323"
echo ""
echo "3. Query status (type in telnet session):"
echo "   STATUS"
echo ""
echo "4. Set up auto-start (optional):"
echo "   mkdir -p $HOME/printer-monitor"
echo "   cp printer_monitor.py $HOME/printer-monitor/"
echo "   sudo systemctl enable printer-monitor@$USER.service"
echo "   sudo systemctl start printer-monitor@$USER.service"
echo ""
echo "5. Check service status:"
echo "   sudo systemctl status printer-monitor@$USER.service"
echo "   journalctl -u printer-monitor@$USER.service -f"
echo ""
