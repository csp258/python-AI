#!/bin/bash
SPASS='123456'

source /opt/stack/devstack/openrc admin admin
export OS_PASSWORD=admin123

echo "=== Step 1: Stop VMs ==="
for vm in vm1 vm2 vm3; do
    openstack server stop $vm 2>&1
done
echo "Waiting for shutdown..."
for i in $(seq 1 30); do
    STATUS=$(openstack server list -f value -c Status 2>/dev/null)
    echo "[$i] $STATUS"
    if ! echo "$STATUS" | grep -q "ACTIVE"; then
        break
    fi
    sleep 3
done

for dom in instance-00000001 instance-00000002 instance-00000003; do
    STATE=$(echo "$SPASS" | sudo -S virsh domstate $dom 2>/dev/null)
    if [ "$STATE" = "running" ]; then
        echo "$SPASS" | sudo -S virsh destroy $dom 2>/dev/null || true
    fi
done
echo "VMs stopped"

echo ""
echo "=== Step 2: Prepare rc.local and verification script ==="
# Create rc.local content
cat > /tmp/rc_local_content << 'RCLOCAL'
#!/bin/sh -e
# Run cluster verification after boot
sleep 30
su - ubuntu -c '/home/ubuntu/verify_cluster.sh 2>&1 | tee /home/ubuntu/verify_output.txt' &
exit 0
RCLOCAL

echo "Files prepared"

echo ""
echo "=== Step 3: Mount each VM and add boot scripts ==="
echo "$SPASS" | sudo -S modprobe nbd max_part=8 2>&1 || true

declare -A VM_DISKS
VM_DISKS["instance-00000001"]="vm1"
VM_DISKS["instance-00000002"]="vm2"
VM_DISKS["instance-00000003"]="vm3"

for DOM in instance-00000001 instance-00000002 instance-00000003; do
    VM_NAME="${VM_DISKS[$DOM]}"
    DISK=$(echo "$SPASS" | sudo -S virsh domblklist $DOM 2>/dev/null | grep vda | awk '{print $2}')

    if [ -z "$DISK" ] || [ ! -f "$DISK" ]; then
        echo "ERROR: disk not found for $DOM"
        continue
    fi

    echo "--- $DOM -> $VM_NAME ---"

    NBD=/dev/nbd1
    echo "$SPASS" | sudo -S qemu-nbd --disconnect $NBD 2>/dev/null || true
    sleep 1
    echo "$SPASS" | sudo -S qemu-nbd --connect=$NBD "$DISK" 2>&1
    sleep 2

    PART=""
    for p in ${NBD}p1 ${NBD}p2 ${NBD}p3; do
        [ -e "$p" ] || continue
        T=$(echo "$SPASS" | sudo -S blkid $p 2>/dev/null | grep -oE 'TYPE="[^"]+"')
        if echo "$T" | grep -qE 'ext[234]'; then
            PART=$p
            break
        fi
    done

    if [ -z "$PART" ]; then
        echo "ERROR: no partition"
        echo "$SPASS" | sudo -S qemu-nbd --disconnect $NBD
        continue
    fi

    MNT=/mnt/$VM_NAME
    echo "$SPASS" | sudo -S mkdir -p $MNT
    echo "$SPASS" | sudo -S mount $PART $MNT 2>&1

    if [ ! -f $MNT/etc/ssh/sshd_config ]; then
        echo "ERROR: mount failed"
        echo "$SPASS" | sudo -S umount $MNT 2>/dev/null
        echo "$SPASS" | sudo -S qemu-nbd --disconnect $NBD
        continue
    fi

    # Install rc.local
    echo "$SPASS" | sudo -S cp /tmp/rc_local_content $MNT/etc/rc.local
    echo "$SPASS" | sudo -S chmod +x $MNT/etc/rc.local
    echo "rc.local installed"

    # Add @reboot cron via /etc/crontab
    echo "$SPASS" | sudo -S bash -c "echo '@reboot ubuntu /home/ubuntu/verify_cluster.sh > /home/ubuntu/verify_output.txt 2>&1' >> $MNT/etc/crontab"
    echo "Cron job added"

    echo "$VM_NAME configured"

    echo "$SPASS" | sudo -S umount $MNT
    echo "$SPASS" | sudo -S qemu-nbd --disconnect $NBD
    sleep 1
done

echo ""
echo "=== Step 4: Start VMs ==="
for vm in vm1 vm2 vm3; do
    openstack server start $vm 2>&1
done

echo "Waiting for VMs to boot and run verification..."
sleep 120

echo ""
echo "=== Step 5: Read verification logs from console ==="
for vm in vm1 vm2 vm3; do
    echo ""
    echo "========== $vm console log (last 40 lines) =========="
    openstack console log show $vm 2>&1 | tail -40
done

echo ""
echo "=== Step 6: Instance status ==="
openstack server list
