#!/bin/bash
SPASS='123456'

echo "=== Test virsh console on vm1 ==="
# Send a command via virsh console - we need to check if serial console works

# First, check the XML for serial console config
echo "=== vm1 XML (serial/console parts) ==="
echo "$SPASS" | sudo -S virsh dumpxml instance-00000001 | grep -A5 -E "serial|console" 2>/dev/null

echo ""
echo "=== Try console access (will timeout if no response) ==="
# Try to send command and get output via console
# Use expect-like approach with timeout
timeout 10 bash -c '
echo "123456" | sudo -S virsh console instance-00000001 --force 2>&1 <<EOF

EOF
' 2>/dev/null || echo "Console timed out or failed"

echo ""
echo "=== Alternative: check if guest agent is available ==="
echo "$SPASS" | sudo -S virsh qemu-agent-command instance-00000001 '{"execute":"guest-info"}' 2>&1 || echo "QEMU guest agent not available"

echo ""
echo "=== Check console log from OpenStack ==="
source /opt/stack/devstack/openrc admin admin
export OS_PASSWORD=admin123
openstack console log show vm1 2>&1 | tail -30
