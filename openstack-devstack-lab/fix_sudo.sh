#!/bin/bash
set -e
SPASS='123456'

echo "=== Fixing stack user sudo ==="

# Kill old stack.sh
echo "$SPASS" | sudo -S pkill -f stack.sh 2>/dev/null || true
sleep 1

# Check current state
echo "Current sudoers.d:"
echo "$SPASS" | sudo -S ls -la /etc/sudoers.d/

# Fix stack sudoers
echo "$SPASS" | sudo -S bash -c 'echo "stack ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/stack'
echo "$SPASS" | sudo -S chmod 440 /etc/sudoers.d/stack

# Test stack sudo
echo "Testing stack sudo:"
sudo -u stack sudo -n whoami && echo "STACK SUDO OK" || echo "STACK SUDO FAILED"

# Check local.conf
echo "=== local.conf ==="
cat /opt/stack/devstack/local.conf

# Check logs dir
echo "=== Logs ==="
ls -la /opt/stack/logs/ 2>/dev/null || echo "NO LOGS DIR"
echo "$SPASS" | sudo -S mkdir -p /opt/stack/logs
echo "$SPASS" | sudo -S chown -R stack:stack /opt/stack

# Remove old logs
echo "$SPASS" | sudo -S rm -f /opt/stack/logs/*.log /opt/stack/logs/*.summary

echo "=== Fix complete ==="
