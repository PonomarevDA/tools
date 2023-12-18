#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo "1. Upload registers"
cat $SCRIPT_DIR/full_registers.yaml | y rb

echo ""
echo "2. Save registers"
y cmd 50 65530
sleep 1

echo ""
echo "3. Reboot"
y cmd 50 65535
sleep 1
