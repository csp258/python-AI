#!/bin/bash
SPASS='123456'

echo "=== Find all instance disks ==="
echo "$SPASS" | sudo -S find /opt/stack/data/nova/instances -name "disk" -type f 2>/dev/null

echo ""
echo "=== Instance directory listing ==="
echo "$SPASS" | sudo -S ls -la /opt/stack/data/nova/instances/ 2>/dev/null

echo ""
echo "=== Try libvirt domain list ==="
echo "$SPASS" | sudo -S virsh list --all 2>/dev/null

echo ""
echo "=== Check libvirt domain XML for disk paths ==="
for dom in instance-00000001 instance-00000002 instance-00000003; do
    echo "--- $dom ---"
    echo "$SPASS" | sudo -S virsh domblklist $dom 2>/dev/null || echo "not found"
done

echo ""
echo "=== Alternative: find all .img files ==="
echo "$SPASS" | sudo -S find /opt/stack/data/nova -name "*.img" -o -name "disk*" 2>/dev/null | head -20

echo ""
echo "=== Check if disks use ceph/rbd ==="
echo "$SPASS" | sudo -S ovs-vsctl show 2>/dev/null | head -5
