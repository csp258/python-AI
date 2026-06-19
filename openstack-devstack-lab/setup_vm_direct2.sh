#!/bin/bash
SPASS='123456'

# Map instance-XXXX to VM name
# instance-00000001 = vm1, instance-00000002 = vm2, instance-00000003 = vm3

echo "=== Load nbd ==="
echo "$SPASS" | sudo -S modprobe nbd max_part=8 2>&1 || true

echo "=== Generate password hash ==="
PASS_HASH=$(python3 -c "import crypt; print(crypt.crypt('openstack', crypt.mksalt(crypt.METHOD_SHA512)))")
echo "Hash: ${PASS_HASH:0:20}..."

declare -A VM_MAP
VM_MAP["instance-00000001"]="vm1"
VM_MAP["instance-00000002"]="vm2"
VM_MAP["instance-00000003"]="vm3"

for DOM in instance-00000001 instance-00000002 instance-00000003; do
    VM_NAME="${VM_MAP[$DOM]}"
    DISK=$(echo "$SPASS" | sudo -S virsh domblklist $DOM 2>/dev/null | grep vda | awk '{print $2}')

    if [ -z "$DISK" ] || [ ! -f "$DISK" ]; then
        echo "Disk for $DOM ($VM_NAME) not found: $DISK"
        continue
    fi

    echo ""
    echo "=== $DOM -> $VM_NAME: $DISK ==="

    NBD=/dev/nbd1
    echo "$SPASS" | sudo -S qemu-nbd --disconnect $NBD 2>/dev/null || true
    sleep 1

    echo "$SPASS" | sudo -S qemu-nbd --connect=$NBD "$DISK" 2>&1
    sleep 2

    # Find root partition
    PART=""
    for p in ${NBD}p1 ${NBD}p2 ${NBD}p3 $NBD; do
        [ -e "$p" ] || continue
        T=$(echo "$SPASS" | sudo -S blkid $p 2>/dev/null | grep -oE 'TYPE="[^"]+"')
        if echo "$T" | grep -qE 'ext[234]|xfs'; then
            PART=$p
            break
        fi
    done

    if [ -z "$PART" ]; then
        echo "No filesystem partition found"
        echo "$SPASS" | sudo -S qemu-nbd --disconnect $NBD
        continue
    fi

    echo "Root partition: $PART"
    echo "$SPASS" | sudo -S mkdir -p /mnt/$VM_NAME
    echo "$SPASS" | sudo -S mount $PART /mnt/$VM_NAME 2>&1

    if [ ! -f /mnt/$VM_NAME/etc/ssh/sshd_config ]; then
        echo "ERROR: not a root filesystem"
        ls /mnt/$VM_NAME/ 2>/dev/null
        echo "$SPASS" | sudo -S umount /mnt/$VM_NAME 2>/dev/null
        echo "$SPASS" | sudo -S qemu-nbd --disconnect $NBD
        continue
    fi

    echo "Mounted OK"

    # Enable password auth
    echo "$SPASS" | sudo -S sed -i 's/^PasswordAuthentication[[:space:]]\+no/PasswordAuthentication yes/' /mnt/$VM_NAME/etc/ssh/sshd_config 2>/dev/null || true
    if ! grep -q '^PasswordAuthentication yes' /mnt/$VM_NAME/etc/ssh/sshd_config; then
        echo "$SPASS" | sudo -S bash -c "echo 'PasswordAuthentication yes' >> /mnt/$VM_NAME/etc/ssh/sshd_config"
    fi
    echo "SSH config: $(grep PasswordAuth /mnt/$VM_NAME/etc/ssh/sshd_config)"

    # Set ubuntu password
    echo "$SPASS" | sudo -S sed -i "s|^ubuntu:[^:]*:|ubuntu:${PASS_HASH}:|" /mnt/$VM_NAME/etc/shadow
    echo "Shadow: $(echo "$SPASS" | sudo -S grep ubuntu /mnt/$VM_NAME/etc/shadow | cut -c1-50)..."

    # Cleanup
    echo "$SPASS" | sudo -S umount /mnt/$VM_NAME
    echo "$SPASS" | sudo -S qemu-nbd --disconnect $NBD
    sleep 1
done

echo ""
echo "=== Done. Rebooting VMs... ==="
source /opt/stack/devstack/openrc admin admin
export OS_PASSWORD=admin123
for vm in vm1 vm2 vm3; do
    openstack server reboot $vm 2>&1 || true
done

echo "Waiting for VMs to boot..."
sleep 40

echo "=== Status ==="
openstack server list
