#!/bin/bash
set -e

# Clean previous failed install
cd /opt/stack/devstack
./clean.sh 2>/dev/null || true
rm -rf /opt/stack/requirements /opt/stack/data /opt/stack/status /opt/stack/logs

# Write new local.conf without GIT_BASE override
cat > /opt/stack/devstack/local.conf << 'ENDCONF'
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

chown stack:stack /opt/stack/devstack/local.conf
echo "=== Config updated ==="
cat /opt/stack/devstack/local.conf
echo "=== Running stack.sh ==="
cd /opt/stack/devstack
./stack.sh
