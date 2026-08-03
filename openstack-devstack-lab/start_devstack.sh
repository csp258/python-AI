#!/bin/bash
set -e
SPASS='123456'

echo "=== Checking requiretty ==="
echo "$SPASS" | sudo -S grep -i requiretty /etc/sudoers /etc/sudoers.d/* 2>/dev/null || echo "requiretty not found"

echo "=== Adding !requiretty for stack user ==="
echo "$SPASS" | sudo -S bash -c 'echo "Defaults:stack !requiretty" > /etc/sudoers.d/stack_tty'
echo "$SPASS" | sudo -S chmod 440 /etc/sudoers.d/stack_tty

echo "=== Clean previous run ==="
cd /opt/stack/devstack
if [ -f .stackenv ]; then
    echo "$SPASS" | sudo -S -u stack ./clean.sh 2>&1 || true
fi
# Ensure clean state
echo "$SPASS" | sudo -S rm -rf /opt/stack/status /opt/stack/data /opt/stack/requirements /opt/stack/*venv* /opt/stack/glance /opt/stack/cinder /opt/stack/keystone /opt/stack/placement /opt/stack/nova /opt/stack/neutron /opt/stack/horizon /opt/stack/noVNC 2>/dev/null || true
echo "$SPASS" | sudo -S mkdir -p /opt/stack/logs
echo "$SPASS" | sudo -S chown -R stack:stack /opt/stack
echo "$SPASS" | sudo -S rm -f /opt/stack/logs/*.log /opt/stack/logs/*.summary

echo "=== Verify local.conf ==="
cat /opt/stack/devstack/local.conf

echo "=== Check that sudo is non-interactive for stack ==="
echo "$SPASS" | sudo -S -u stack sudo -n whoami && echo "SUDO VERIFIED" || echo "SUDO FAILED"

echo "=== Starting DevStack stack.sh ==="
# Use script to provide a pseudo-TTY for sudo
echo "$SPASS" | sudo -S -u stack nohup script -q -c 'cd /opt/stack/devstack && ./stack.sh' /tmp/devstack_script.log > /tmp/devstack_nohup.log 2>&1 &
PID=$!
echo "stack.sh started with PID: $PID"
echo ""
echo "Monitor commands:"
echo "  tail -f /opt/stack/logs/stack.sh.log.*"
echo "  tail -f /tmp/devstack_nohup.log"
echo "  pgrep -f stack.sh"
echo ""
echo "=== Launched ==="
