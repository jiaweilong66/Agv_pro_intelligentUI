#!/bin/bash

echo "========================================="
echo "Checking available serial ports"
echo "========================================="

echo ""
echo "All /dev/tty* devices:"
ls -la /dev/tty* | grep -E "(ACM|USB)"

echo ""
echo "Python serial port detection:"
python3 << 'EOF'
import serial.tools.list_ports
ports = serial.tools.list_ports.comports()
for port in ports:
    print(f"Port: {port.device}")
    print(f"  Description: {port.description}")
    print(f"  Hardware ID: {port.hwid}")
    print()
EOF

echo "========================================="
