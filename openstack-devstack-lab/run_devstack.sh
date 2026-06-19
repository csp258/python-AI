#!/bin/bash
# Write config, prepare env, and start DevStack stack.sh
set -e

SPASS='123456'
esudo() { echo "$SPASS" | sudo -S "$@" 2>&1; }

# Fix git ownership
git config --global --add safe.directory /opt/stack/devstack 2>/dev/null || true

echo "=== Step 1: Write local.conf ==="
cat > /tmp/local_conf_tmp << 'ENDCONF'
[[local|localrc]]
HOST_IP=192.168.153.128
ADMIN_PASSWORD=admin123
DATABASE_PASSWORD=admin123
RABBIT_PASSWORD=admin123
SERVICE_PASSWORD=admin123
LOGFILE=/opt/stack/logs/stack.sh.log
LOGDAYS=1
SWIFT_ENABLE=False
HEAT_ENABLE=False
CEILOMETER_ENABLE=False
ENABLED_SERVICES=key,n-api,n-cpu,n-cond,n-sch,n-novnc,n-api-meta,placement-api,placement-client,g-api,c-sch,c-api,c-vol,horizon,q-svc,q-ovn-metadata-agent,ovn-controller,ovn-northd,ovs-vswitchd,ovsdb-server
ENDCONF

esudo cp /tmp/local_conf_tmp /opt/stack/devstack/local.conf
esudo chown stack:stack /opt/stack/devstack/local.conf
echo "local.conf written:"
cat /tmp/local_conf_tmp

echo "=== Step 2: Create /opt/stack/logs ==="
esudo mkdir -p /opt/stack/logs
esudo chown -R stack:stack /opt/stack
echo "logs dir created"

echo "=== Step 3: Clean any previous run ==="
cd /opt/stack/devstack
if [ -f .stackenv ]; then
    echo "Cleaning previous run..."
    sudo -u stack ./clean.sh 2>&1 || true
fi
esudo rm -rf /opt/stack/status /opt/stack/data /opt/stack/requirements /opt/stack/*venv* /opt/stack/glance /opt/stack/cinder /opt/stack/keystone /opt/stack/placement /opt/stack/nova /opt/stack/neutron /opt/stack/horizon 2>/dev/null || true
esudo mkdir -p /opt/stack/logs
esudo chown -R stack:stack /opt/stack
echo "cleanup done"

echo "=== Step 4: Start stack.sh in background ==="
sudo -u stack nohup bash -c 'cd /opt/stack/devstack && ./stack.sh' > /tmp/devstack_output.log 2>&1 &
PID=$!
echo "stack.sh started with PID: $PID"
echo "Monitor with: tail -f /opt/stack/logs/stack.sh.log.*"
echo "Or: tail -f /tmp/devstack_output.log"

echo "=== DONE - DevStack is running ==="
