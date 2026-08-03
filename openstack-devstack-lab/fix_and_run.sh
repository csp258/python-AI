#!/bin/bash
# Fix issues and restart DevStack
set -e
SPASS='123456'

echo "=== Killing unattended-upgrades ==="
echo "$SPASS" | sudo -S pkill -9 unattended-upgr 2>/dev/null || true
echo "$SPASS" | sudo -S pkill -9 apt-get 2>/dev/null || true
echo "$SPASS" | sudo -S pkill -9 apt 2>/dev/null || true
sleep 2

echo "=== Removing apt locks ==="
echo "$SPASS" | sudo -S rm -f /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/lib/apt/lists/lock 2>/dev/null || true
echo "$SPASS" | sudo -S dpkg --configure -a 2>/dev/null || true

echo "=== Disabling unattended-upgrades ==="
echo "$SPASS" | sudo -S systemctl stop unattended-upgrades 2>/dev/null || true
echo "$SPASS" | sudo -S systemctl disable unattended-upgrades 2>/dev/null || true
echo "$SPASS" | sudo -S rm -f /etc/apt/apt.conf.d/20auto-upgrades 2>/dev/null || true
echo "$SPASS" | sudo -S bash -c 'cat > /etc/apt/apt.conf.d/99disable-auto-update << EOF
APT::Periodic::Update-Package-Lists "0";
APT::Periodic::Unattended-Upgrade "0";
EOF'

echo "=== Removing Docker apt source (blocked in China) ==="
echo "$SPASS" | sudo -S rm -f /etc/apt/sources.list.d/docker.list 2>/dev/null || true
echo "$SPASS" | sudo -S rm -f /etc/apt/sources.list.d/*docker* 2>/dev/null || true
echo "$SPASS" | sudo -S rm -f /etc/apt/keyrings/docker.gpg 2>/dev/null || true

echo "=== Testing apt ==="
echo "$SPASS" | sudo -S apt-get update -qq 2>&1 | tail -3
echo "apt OK"

echo "=== Clean DevStack state ==="
cd /opt/stack/devstack
if [ -f .stackenv ]; then
    echo "$SPASS" | sudo -S -u stack ./clean.sh 2>&1 || true
fi
echo "$SPASS" | sudo -S rm -rf /opt/stack/status /opt/stack/data /opt/stack/requirements /opt/stack/*venv* /opt/stack/glance /opt/stack/cinder /opt/stack/keystone /opt/stack/placement /opt/stack/nova /opt/stack/neutron /opt/stack/horizon /opt/stack/noVNC /opt/stack/*rc /opt/stack/.my.cnf 2>/dev/null || true
echo "$SPASS" | sudo -S mkdir -p /opt/stack/logs
echo "$SPASS" | sudo -S chown -R stack:stack /opt/stack
echo "$SPASS" | sudo -S rm -f /opt/stack/logs/*.log /opt/stack/logs/*.summary

echo "=== Verify local.conf ==="
cat /opt/stack/devstack/local.conf

echo "=== Starting DevStack with proper TERM ==="
# Use TERM=linux instead of unknown to avoid tput errors
echo "$SPASS" | sudo -S -u stack nohup bash -c 'export TERM=linux; cd /opt/stack/devstack && ./stack.sh' > /tmp/devstack_nohup.log 2>&1 &
PID=$!
echo "stack.sh started with PID: $PID"
echo "Monitor: tail -f /opt/stack/logs/stack.sh.log.*"

echo "=== Launched ==="
