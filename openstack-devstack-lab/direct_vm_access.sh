#!/bin/bash
# Shut down vm1, mount its disk, set password, restart
set -e
SPASS='123456'

echo "=== Step 1: Shut down vm1 ==="
echo "$SPASS" | sudo -S virsh destroy instance-00000001 2>/dev/null || true
sleep 3

echo "=== Step 2: Mount vm1 disk ==="
echo "$SPASS" | sudo -S modprobe nbd
echo "$SPASS" | sudo -S qemu-nbd --connect=/dev/nbd0 /opt/stack/data/nova/instances/af4f1cd8-6d91-4779-b192-159046d70c63/disk 2>&1 || true
sleep 1

echo "=== Step 3: List partitions ==="
echo "$SPASS" | sudo -S fdisk -l /dev/nbd0 2>/dev/null | head -15

echo "=== Step 4: Mount /dev/nbd0p1 ==="
echo "$SPASS" | sudo -S mkdir -p /mnt/vm1
echo "$SPASS" | sudo -S mount /dev/nbd0p1 /mnt/vm1 2>&1 || echo "trying direct mount..."
# Cloud images might have the filesystem directly on nbd0
echo "$SPASS" | sudo -S mount /dev/nbd0 /mnt/vm1 2>&1 || true

echo "=== Step 5: Check what we have ==="
echo "$SPASS" | sudo -S ls /mnt/vm1/ 2>/dev/null

echo "=== DONE ==="
