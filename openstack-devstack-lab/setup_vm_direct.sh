#!/bin/bash
# Mount VM disks via qemu-nbd, enable password SSH
SPASS='123456'

echo "=== Load nbd kernel module ==="
echo "$SPASS" | sudo -S modprobe nbd max_part=8 2>&1 || true

# Get instance disk paths
source /opt/stack/devstack/openrc admin admin
export OS_PASSWORD=admin123

echo "=== Generate password hash ==="
PASS_HASH=$(python3 -c "import crypt; print(crypt.crypt('openstack', crypt.mksalt(crypt.METHOD_SHA512)))")
echo "Hash: $PASS_HASH"

# Collect disk paths
declare -A DISKS
while IFS='|' read -r uuid name; do
    name=$(echo "$name" | xargs)
    uuid=$(echo "$uuid" | xargs)
    [ -z "$name" ] && continue
    DISK="/opt/stack/data/nova/instances/${uuid}/disk"
    if [ -f "$DISK" ]; then
        DISKS["$name"]="$DISK"
        echo "Found: $name -> $DISK"
    fi
done < <(openstack server list -f value -c ID -c Name)

setup_vm() {
    local VM_NAME=$1
    local DISK_PATH=$2
    local NBD_DEV="/dev/nbd1"

    echo ""
    echo "=== Setting up $VM_NAME: $DISK_PATH ==="

    echo "$SPASS" | sudo -S qemu-nbd --disconnect $NBD_DEV 2>/dev/null || true
    sleep 1

    echo "$SPASS" | sudo -S qemu-nbd --connect=$NBD_DEV "$DISK_PATH" 2>&1
    sleep 2

    # Find root partition
    PART=""
    for p in ${NBD_DEV}p1 ${NBD_DEV}p2 $NBD_DEV; do
        if [ -e "$p" ]; then
            FS=$(echo "$SPASS" | sudo -S blkid $p 2>/dev/null | grep -oE 'TYPE="[^"]+"' | head -1)
            if echo "$FS" | grep -qE "ext|xfs|btrfs"; then
                PART=$p
                break
            fi
        fi
    done

    if [ -z "$PART" ]; then
        echo "ERROR: Could not find filesystem on $NBD_DEV"
        return 1
    fi

    echo "Using partition: $PART"

    echo "$SPASS" | sudo -S mkdir -p /mnt/${VM_NAME}
    echo "$SPASS" | sudo -S mount $PART /mnt/${VM_NAME} 2>&1 || {
        echo "Mount failed, trying direct mount"
        echo "$SPASS" | sudo -S mount $NBD_DEV /mnt/${VM_NAME} 2>&1 || return 1
    }

    if [ ! -f /mnt/${VM_NAME}/etc/ssh/sshd_config ]; then
        echo "ERROR: Mount failed - no /etc/ssh/sshd_config found"
        ls /mnt/${VM_NAME}/ 2>/dev/null
        return 1
    fi

    echo "Mounted OK"

    # Enable password authentication
    echo "$SPASS" | sudo -S sed -i 's/^PasswordAuthentication[[:space:]]\+no/PasswordAuthentication yes/' /mnt/${VM_NAME}/etc/ssh/sshd_config 2>/dev/null || true
    if ! grep -q "^PasswordAuthentication yes" /mnt/${VM_NAME}/etc/ssh/sshd_config; then
        echo "PasswordAuthentication yes" | echo "$SPASS" | sudo -S tee -a /mnt/${VM_NAME}/etc/ssh/sshd_config > /dev/null
    fi
    echo "SSH password auth: $(grep PasswordAuthentication /mnt/${VM_NAME}/etc/ssh/sshd_config)"

    # Set ubuntu password
    echo "$SPASS" | sudo -S sed -i "s|^ubuntu:[^:]*:|ubuntu:${PASS_HASH}:|" /mnt/${VM_NAME}/etc/shadow
    echo "Shadow updated: $(echo "$SPASS" | sudo -S grep ubuntu /mnt/${VM_NAME}/etc/shadow | cut -c1-40)..."

    # Enable root login just in case
    echo "$SPASS" | sudo -S sed -i 's/^#PermitRootLogin prohibit-password/PermitRootLogin yes/' /mnt/${VM_NAME}/etc/ssh/sshd_config 2>/dev/null || true

    echo "$VM_NAME setup complete"

    # Cleanup
    echo "$SPASS" | sudo -S umount /mnt/${VM_NAME}
    echo "$SPASS" | sudo -S qemu-nbd --disconnect $NBD_DEV
    sleep 1
}

for vm in vm1 vm2 vm3; do
    if [ -n "${DISKS[$vm]}" ]; then
        setup_vm "$vm" "${DISKS[$vm]}"
    else
        echo "Disk for $vm not found - skipping"
    fi
done

echo ""
echo "=== Rebooting VMs to apply changes ==="
for vm in vm1 vm2 vm3; do
    echo "Rebooting $vm..."
    openstack server reboot $vm 2>&1 || true
done

echo "Waiting 30s for VMs to start..."
sleep 30

echo "=== Instance status ==="
openstack server list
