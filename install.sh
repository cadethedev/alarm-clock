#!/bin/bash
# Installation script for sunrise alarm clock

echo "🌅 Installing Sunrise Alarm Clock..."

# Get the current directory
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📁 Installation directory: $INSTALL_DIR"

# Create unified alarm system service
echo "Creating unified alarm system service..."
sudo tee /etc/systemd/system/alarm-system.service > /dev/null <<EOF
[Unit]
Description=Sunrise Alarm Clock System (Unified)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/alarm_system.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create Flask web service
echo "Creating Flask web service..."
sudo tee /etc/systemd/system/alarm-web.service > /dev/null <<EOF
[Unit]
Description=Alarm Clock Web Interface
After=network.target

[Service]
Type=simple
User=cadev
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/web_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable services
echo "Enabling services..."
sudo systemctl enable alarm-system.service
sudo systemctl enable alarm-web.service

# Start services
echo "Starting services..."
sudo systemctl start alarm-system.service
sudo systemctl start alarm-web.service

echo ""
echo "✅ Installation complete!"
echo ""
echo "Services installed:"
echo "  - alarm-system.service (Unified: alarm checker, button handler, sunrise animation)"
echo "  - alarm-web.service (Web interface on port 5000)"
echo ""
echo "Button controls:"
echo "  - Hold 1s → White appears"
echo "  - Keep holding to 5s → Red flash = Alarm disabled"
echo "  - Release before 5s → Enter alarm setup menu"
echo "  - During alarm → Any press = Stop"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status alarm-system    # Check system status"
echo "  sudo systemctl status alarm-web       # Check web status"
echo "  sudo journalctl -u alarm-system -f    # View system logs"
echo "  sudo journalctl -u alarm-web -f       # View web logs"
echo ""
echo "Set alarm:"
echo "  - Visit http://$(hostname -I | awk '{print $1}'):5000"
echo "  - Or hold button for 1-5 seconds"
echo ""
