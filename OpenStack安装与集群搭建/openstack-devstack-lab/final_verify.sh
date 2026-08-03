#!/bin/bash
source /opt/stack/devstack/openrc admin admin
export OS_PASSWORD=admin123

echo "========================================"
echo "  SS3014 Lab 16 - Final Verification"
echo "========================================"
echo ""

echo "=== 1. OpenStack Services ==="
openstack service list -f value -c Name -c Type -c Enabled 2>/dev/null | head -10

echo ""
echo "=== 2. Instance List ==="
openstack server list

echo ""
echo "=== 3. Floating IPs ==="
openstack floating ip list -f value -c "Floating IP Address" -c "Fixed IP Address"

echo ""
echo "=== 4. Check Horizon ==="
curl -s -o /dev/null -w "HTTP %{http_code}" http://192.168.153.128/dashboard 2>/dev/null || echo "Horizon unreachable"

echo ""
echo "=== 5. Console log verification from VM1 ==="
openstack console log show vm1 2>&1 | grep -E "SSH to|SSH_OK|SSH_FAILED|Verification complete"

echo ""
echo "=== 6. Console log verification from VM2 ==="
openstack console log show vm2 2>&1 | grep -E "SSH to|SSH_OK|SSH_FAILED|Verification complete"

echo ""
echo "=== 7. Console log verification from VM3 ==="
openstack console log show vm3 2>&1 | grep -E "SSH to|SSH_OK|SSH_FAILED|Verification complete"

echo ""
echo "=== 8. Hostname verification ==="
for vm in vm1 vm2 vm3; do
    echo -n "$vm hostname: "
    openstack console log show $vm 2>&1 | grep "$vm login" | head -1
done

echo ""
echo "========================================"
echo "  VERIFICATION COMPLETE"
echo "========================================"
