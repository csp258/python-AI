#!/bin/bash
# Final DevStack setup with fixed service list
set -e
SPASS='123456'

echo "=== Fixing local.conf - add mysql and rabbit ==="
cat > /tmp/local_conf_fix << 'ENDCONF'
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
ENABLED_SERVICES=mysql,rabbit,key,n-api,n-cpu,n-cond,n-sch,n-novnc,n-api-meta,placement-api,placement-client,g-api,c-sch,c-api,c-vol,horizon,q-svc,q-ovn-metadata-agent,ovn-controller,ovn-northd,ovs-vswitchd,ovsdb-server
ENDCONF

echo "$SPASS" | sudo -S cp /tmp/local_conf_fix /opt/stack/devstack/local.conf
echo "$SPASS" | sudo -S chown stack:stack /opt/stack/devstack/local.conf
echo "local.conf:"
cat /opt/stack/devstack/local.conf

echo "=== Clean state ==="
cd /opt/stack/devstack
if [ -f .stackenv ]; then
    echo "$SPASS" | sudo -S -u stack ./clean.sh 2>&1 | tail -5 || true
fi
echo "$SPASS" | sudo -S rm -rf /opt/stack/status /opt/stack/data /opt/stack/requirements /opt/stack/*venv* /opt/stack/glance /opt/stack/cinder /opt/stack/keystone /opt/stack/placement /opt/stack/nova /opt/stack/neutron /opt/stack/horizon /opt/stack/noVNC /opt/stack/*rc /opt/stack/.my.cnf 2>/dev/null || true
echo "$SPASS" | sudo -S mkdir -p /opt/stack/logs
echo "$SPASS" | sudo -S chown -R stack:stack /opt/stack
echo "$SPASS" | sudo -S rm -f /opt/stack/logs/*.log /opt/stack/logs/*.summary /opt/stack/logs/*.txt

echo "=== Starting DevStack ==="
echo "$SPASS" | sudo -S -u stack nohup bash -c 'export TERM=linux; cd /opt/stack/devstack && ./stack.sh' > /tmp/devstack_nohup.log 2>&1 &
PID=$!
echo "PID: $PID"
echo "Monitor: tail -f /opt/stack/logs/stack.sh.log"
echo "=== Launched ==="
