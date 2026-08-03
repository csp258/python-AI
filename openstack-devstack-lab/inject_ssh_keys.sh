#!/bin/bash
SPASS='123456'

source /opt/stack/devstack/openrc admin admin
export OS_PASSWORD=admin123

echo "=== Step 1: Stop all VMs ==="
for vm in vm1 vm2 vm3; do
    echo "Stopping $vm..."
    openstack server stop $vm --wait 2>&1 | tail -1
done
echo "All VMs stopped"

echo ""
echo "=== Step 2: Generate shared SSH key ==="
SSH_DIR="/tmp/vm_ssh_key"
rm -rf $SSH_DIR
mkdir -p $SSH_DIR
ssh-keygen -t rsa -N "" -f $SSH_DIR/id_rsa -C "cluster-key" 2>&1
PUBKEY=$(cat $SSH_DIR/id_rsa.pub)
echo "Key generated"

echo ""
echo "=== Step 3: Generate password hash ==="
PASS_HASH=$(python3 -c "import crypt; print(crypt.crypt('openstack', crypt.mksalt(crypt.METHOD_SHA512)))")

echo ""
echo "=== Step 4: Create hosts file content ==="
HOSTS_CONTENT="127.0.0.1 localhost
10.0.0.39 vm1
10.0.0.55 vm2
10.0.0.17 vm3"

echo ""
echo "=== Step 5: Create verification script ==="
cat > /tmp/verify_cluster.sh << 'VERIFYEOF'
#!/bin/bash
echo "=== $(hostname) cluster verification ==="
echo "My IP: $(hostname -I)"
echo ""
echo "=== /etc/hosts ==="
cat /etc/hosts
echo ""
for target in vm1 vm2 vm3; do
    echo "--- SSH to $target ---"
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 $target "hostname && echo SSH_OK" 2>&1 || echo "SSH_FAILED"
done
echo "=== Verification complete ==="
VERIFYEOF

echo "=== Step 6: Mount and configure each VM ==="
echo "$SPASS" | sudo -S modprobe nbd max_part=8 2>&1 || true

declare -A VM_DISKS
VM_DISKS["instance-00000001"]="vm1"
VM_DISKS["instance-00000002"]="vm2"
VM_DISKS["instance-00000003"]="vm3"

for DOM in instance-00000001 instance-00000002 instance-00000003; do
    VM_NAME="${VM_DISKS[$DOM]}"

    DISK=$(echo "$SPASS" | sudo -S virsh domblklist $DOM 2>/dev/null | grep vda | awk '{print $2}')

    if [ -z "$DISK" ] || [ ! -f "$DISK" ]; then
        echo "ERROR: disk for $DOM ($VM_NAME) not found"
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
        if echo "$T" | grep -qE 'ext[234]'; then
            PART=$p
            break
        fi
    done

    if [ -z "$PART" ]; then
        T=$(echo "$SPASS" | sudo -S blkid $NBD 2>/dev/null | grep -oE 'TYPE="[^"]+"')
        if echo "$T" | grep -qE 'ext[234]'; then
            PART=$NBD
        fi
    fi

    if [ -z "$PART" ]; then
        echo "ERROR: no ext2/3/4 partition found"
        echo "$SPASS" | sudo -S blkid ${NBD}* 2>/dev/null || true
        echo "$SPASS" | sudo -S qemu-nbd --disconnect $NBD
        continue
    fi

    echo "Partition: $PART"

    echo "$SPASS" | sudo -S mkdir -p /mnt/$VM_NAME
    echo "$SPASS" | sudo -S mount $PART /mnt/$VM_NAME 2>&1

    if [ ! -f /mnt/$VM_NAME/etc/ssh/sshd_config ]; then
        echo "ERROR: mount failed"
        ls /mnt/$VM_NAME/ 2>/dev/null
        echo "$SPASS" | sudo -S umount /mnt/$VM_NAME 2>/dev/null
        echo "$SPASS" | sudo -S qemu-nbd --disconnect $NBD
        continue
    fi

    echo "Mounted OK"

    # Create .ssh directory with proper permissions
    MNT=/mnt/$VM_NAME
    echo "$SPASS" | sudo -S mkdir -p $MNT/home/ubuntu/.ssh

    # Copy keys
    echo "$SPASS" | sudo -S cp $SSH_DIR/id_rsa $MNT/home/ubuntu/.ssh/id_rsa
    echo "$SPASS" | sudo -S cp $SSH_DIR/id_rsa.pub $MNT/home/ubuntu/.ssh/id_rsa.pub
    echo "$SPASS" | sudo -S cp $SSH_DIR/id_rsa.pub $MNT/home/ubuntu/.ssh/authorized_keys

    # Set permissions
    echo "$SPASS" | sudo -S chmod 700 $MNT/home/ubuntu/.ssh
    echo "$SPASS" | sudo -S chmod 600 $MNT/home/ubuntu/.ssh/id_rsa
    echo "$SPASS" | sudo -S chmod 644 $MNT/home/ubuntu/.ssh/id_rsa.pub
    echo "$SPASS" | sudo -S chmod 644 $MNT/home/ubuntu/.ssh/authorized_keys
    echo "$SPASS" | sudo -S chown -R 1000:1000 $MNT/home/ubuntu/.ssh
    echo "SSH keys installed"

    # Enable password auth
    echo "$SPASS" | sudo -S sed -i 's/^PasswordAuthentication[[:space:]]\+no/PasswordAuthentication yes/' $MNT/etc/ssh/sshd_config 2>/dev/null || true
    if ! grep -q '^PasswordAuthentication yes' $MNT/etc/ssh/sshd_config; then
        echo "$SPASS" | sudo -S bash -c "echo 'PasswordAuthentication yes' >> $MNT/etc/ssh/sshd_config"
    fi
    echo "Password auth: $(grep PasswordAuth $MNT/etc/ssh/sshd_config)"

    # Set ubuntu password
    echo "$SPASS" | sudo -S sed -i "s|^ubuntu:[^:]*:|ubuntu:${PASS_HASH}:|" $MNT/etc/shadow
    echo "Password set"

    # Add hosts entries
    echo "$SPASS" | sudo -S bash -c "echo '10.0.0.39 vm1' >> $MNT/etc/hosts"
    echo "$SPASS" | sudo -S bash -c "echo '10.0.0.55 vm2' >> $MNT/etc/hosts"
    echo "$SPASS" | sudo -S bash -c "echo '10.0.0.17 vm3' >> $MNT/etc/hosts"
    echo "Hosts updated"

    # Copy verification script
    echo "$SPASS" | sudo -S cp /tmp/verify_cluster.sh $MNT/home/ubuntu/verify_cluster.sh
    echo "$SPASS" | sudo -S chmod +x $MNT/home/ubuntu/verify_cluster.sh
    echo "$SPASS" | sudo -S chown 1000:1000 $MNT/home/ubuntu/verify_cluster.sh
    echo "Verification script installed"

    echo "$VM_NAME: ALL DONE"

    echo "$SPASS" | sudo -S umount $MNT
    echo "$SPASS" | sudo -S qemu-nbd --disconnect $NBD
    sleep 1
done

echo ""
echo "=== Step 7: Start VMs ==="
for vm in vm1 vm2 vm3; do
    openstack server start $vm --wait 2>&1 | tail -1
done

echo ""
echo "=== Step 8: Wait for VMs to boot ==="
sleep 60

echo ""
echo "=== Step 9: Instance status ==="
openstack server list

echo ""
echo "=== Step 10: Test SSH from virsh console ==="
# Try accessing vm1 via console and run verification
echo "Accessing vm1 via virsh console..."
echo "$SPASS" | sudo -S bash -c '
echo "" | timeout 5 virsh console instance-00000001 --force 2>&1 || true
'

echo ""
echo "=== Step 11: Console log tail ==="
openstack console log show vm1 2>&1 | tail -15

echo ""
echo "=== ALL DONE ==="
echo "Password: openstack"
echo "SSH key: /tmp/vm_ssh_key/id_rsa"
echo "Internal IPs: vm1=10.0.0.39, vm2=10.0.0.55, vm3=10.0.0.17"
