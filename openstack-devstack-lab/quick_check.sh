#!/bin/bash
source /opt/stack/devstack/openrc admin admin
export OS_PASSWORD=admin123

echo "=== 1. Services ==="
openstack service list 2>&1 | head -12

echo ""
echo "=== 2. Instances ==="
openstack server list 2>&1

echo ""
echo "=== 3. Horizon check ==="
curl -s -o /dev/null -w "Horizon HTTP: %{http_code}\n" http://192.168.153.128/dashboard

echo ""
echo "=== 4. Systemd services ==="
systemctl --user status devstack@* 2>/dev/null | grep -E "Active|Unit" | head -10
