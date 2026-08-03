#!/bin/bash
SPASS='123456'

source /opt/stack/devstack/openrc admin admin
export OS_PASSWORD=admin123

echo "=== Step 1: Shut down all VMs ==="
openstack server stop vm1 --wait 2>&1 | tail -1
openstack server stop vm2 --wait 2>&1 | tail -1
openstack server stop vm3 --wait 2>&1 | tail -1
echo "All VMs stopped"

echo ""
echo "=== Step 2: Generate password hash ==="
PASS_HASH=$(python3 -c "import crypt; print(crypt.crypt('openstack', crypt.mksalt(crypt.METHOD.SHA512)))")
echo "Hash: ${PASS_HASH:0:20}..."

echo ""
echo "=== Step 3: Mount and modify each VM disk ==="

declare -A VM_MAP
VM_MAP["instance-00000001"]="vm1"
VM_MAP["instance-00000002"]="vm2"
VM_MAP["instance-00000003"]="vm3"

echo "$SPASS" | sudo -S modprobe nbd max_part=8 2>&1 || true

for DOM in instance-00000001 instance-00000002 instance-00000003; do
    VM_NAME="${VM_MAP[$DOM]}"

    # Get disk path from virsh
    DISK=$(echo "$SPASS" | sudo -S virsh domblklist $DOM 2>/dev/null | grep vda | awk '{print $2}')

    if [ -z "$DISK" ] || [ ! -f "$DISK" ]; then
        echo "ERROR: disk for $DOM not found: $DISK"
        continue
    fi

    echo ""
    echo "--- $DOM -> $VM_NAME: $DISK ---"

    NBD=/dev/nbd1
    echo "$SPASS" | sudo -S qemu-nbd --disconnect $NBD 2>/dev/null || true
    sleep 1

    echo "$SPASS" | sudo -S qemu-nbd --connect=$NBD "$DISK" 2>&1
    sleep 2

    # Find root partition
    PART=""
    for p in ${NBD}p1 ${NBD}p2 ${NBD}p3; do
        [ -e "$p" ] || continue
        T=$(echo "$SPASS" | sudo -S blkid $p 2>/dev/null | grep -oE 'TYPE="[^"]+"')
        if echo "$T" | grep -qE 'ext[234]|xfs'; then
            PART=$p
            break
        fi
    done

    if [ -z "$PART" ]; then
        # Try without partition (whole disk)
        T=$(echo "$SPASS" | sudo -S blkid $NBD 2>/dev/null | grep -oE 'TYPE="[^"]+"')
        if echo "$T" | grep -qE 'ext[234]|xfs'; then
            PART=$NBD
        fi
    fi

    if [ -z "$PART" ]; then
        echo "No partition found, checking all:"
        echo "$SPASS" | sudo -S blkid ${NBD}* 2>/dev/null || true
        echo "$SPASS" | sudo -S qemu-nbd --disconnect $NBD
        continue
    fi

    echo "Root partition: $PART ($(echo "$SPASS" | sudo -S blkid $PART 2>/dev/null | grep -oE 'TYPE="[^"]+"'))"

    echo "$SPASS" | sudo -S mkdir -p /mnt/$VM_NAME
    echo "$SPASS" | sudo -S mount $PART /mnt/$VM_NAME 2>&1

    if [ ! -f /mnt/$VM_NAME/etc/ssh/sshd_config ]; then
        echo "ERROR: mount failed"
        ls /mnt/$VM_NAME/ 2>/dev/null
        echo "$SPASS" | sudo -S umount /mnt/$VM_NAME 2>/dev/null
        echo "$SPASS" | sudo -S qemu-nbd --disconnect $NBD
        continue
    fi

    echo "Mounted OK: $(ls /mnt/$VM_NAME/ | head -10)"

    # Enable password auth
    echo "$SPASS" | sudo -S sed -i 's/^PasswordAuthentication[[:space:]]\+no/PasswordAuthentication yes/' /mnt/$VM_NAME/etc/ssh/sshd_config 2>/dev/null || true
    if ! grep -q '^PasswordAuthentication yes' /mnt/$VM_NAME/etc/ssh/sshd_config; then
        echo "$SPASS" | sudo -S bash -c "echo 'PasswordAuthentication yes' >> /mnt/$VM_NAME/etc/ssh/sshd_config"
    fi

    CONFIGURED=$(grep "PasswordAuthentication" /mnt/$VM_NAME/etc/ssh/sshd_config)
    echo "SSH config: $CONFIGURED"

    # Set ubuntu password
    echo "$SPASS" | sudo -S sed -i "s|^ubuntu:[^:]*:|ubuntu:${PASS_HASH}:|" /mnt/$VM_NAME/etc/shadow

    SHADOW_LINE=$(echo "$SPASS" | sudo -S grep ubuntu /mnt/$VM_NAME/etc/shadow | cut -c1-60)
    echo "Shadow: $SHADOW_LINE..."

    # Cleanup
    echo "$SPASS" | sudo -S umount /mnt/$VM_NAME
    echo "$SPASS" | sudo -S qemu-nbd --disconnect $NBD
    sleep 1
done

echo ""
echo "=== Step 4: Start VMs ==="
openstack server start vm1 --wait 2>&1 | tail -1
openstack server start vm2 --wait 2>&1 | tail -1
openstack server start vm3 --wait 2>&1 | tail -1

echo ""
echo "=== Step 5: Status ==="
openstack server list

echo ""
echo "=== Step 6: Wait for boot ==="
sleep 45

echo ""
echo "=== Step 7: Try SSH ==="
echo "SSH to vm1 via floating IP..."
sshpass -p 'openstack' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@172.24.4.186 "hostname && echo PASSWORD_SSH_OK" 2>&1 || echo "SSH FAILED via floating IP"

echo ""
echo "=== Step 8: Try console log tail ==="
openstack console log show vm1 2>&1 | tail -20
