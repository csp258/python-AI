#!/bin/bash
# Cleanup VM for fresh DevStack install
set -e

SPASS='123456'

esudo() {
    echo "$SPASS" | sudo -S "$@" 2>&1 || echo "[WARN] sudo $1 failed, continuing..."
}

echo "=== Step 1: Stop and remove Juju/LXD ==="
echo "$SPASS" | sudo -S lxc stop juju-897fc1-0 2>/dev/null || true
echo "$SPASS" | sudo -S lxc delete juju-897fc1-0 2>/dev/null || true
echo "LXC cleaned"

echo "=== Step 2: Remove OpenStack snap ==="
echo "$SPASS" | sudo -S snap remove --purge openstack 2>&1 || true

echo "=== Step 3: Remove Juju snap ==="
echo "$SPASS" | sudo -S snap remove --purge juju 2>&1 || true

echo "=== Step 4: Remove LXD snap ==="
echo "$SPASS" | sudo -S snap remove --purge lxd 2>&1 || true

echo "=== Step 5: Clean Docker ==="
echo "$SPASS" | sudo -S docker system prune -af 2>&1 || true

echo "=== Step 6: Clean /opt/stack ==="
echo "$SPASS" | sudo -S rm -rf /opt/stack
echo "$SPASS" | sudo -S mkdir -p /opt/stack

echo "=== Step 7: Remove old caches ==="
rm -rf ~/.cache/pip 2>/dev/null || true

echo "=== Step 8: Disk space ==="
df -h /
echo ""
echo "$SPASS" | sudo -S du -sh /var/lib/lxd 2>/dev/null || echo "no lxd dir"
echo "$SPASS" | sudo -S du -sh /var/lib/docker 2>/dev/null || echo "no docker dir"
echo "$SPASS" | sudo -S du -sh /snap 2>/dev/null || echo "no snap dir"
echo "$SPASS" | sudo -S du -sh /var/lib/snapd 2>/dev/null || echo "no snapd dir"

echo "=== Cleanup complete ==="
