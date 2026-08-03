#!/bin/bash
# Create OpenStack instances for experiment 16
set -e

# Source openrc
source /opt/stack/devstack/openrc admin admin
export OS_PASSWORD=admin123

echo "=== Step 1: Download Ubuntu 22.04 Cloud Image ==="
UBUNTU_IMG_URL="https://mirrors.tuna.tsinghua.edu.cn/ubuntu-cloud-images/jammy/current/jammy-server-cloudimg-amd64.img"
IMG_FILE="/tmp/jammy-server-cloudimg-amd64.img"

if [ ! -f "$IMG_FILE" ]; then
    echo "Downloading Ubuntu cloud image from Tsinghua mirror..."
    wget -q --show-progress "$UBUNTU_IMG_URL" -O "$IMG_FILE" || {
        echo "Tsinghua mirror failed, trying aliyun..."
        wget -q --show-progress "https://mirrors.aliyun.com/ubuntu-cloud-images/jammy/current/jammy-server-cloudimg-amd64.img" -O "$IMG_FILE"
    }
    echo "Download complete: $(ls -lh $IMG_FILE | awk '{print $5}')"
else
    echo "Image already downloaded: $(ls -lh $IMG_FILE | awk '{print $5}')"
fi

echo "=== Step 2: Upload image to Glance ==="
openstack image create "ubuntu-22.04-cloudimg" \
    --file "$IMG_FILE" \
    --disk-format qcow2 \
    --container-format bare \
    --public

echo "=== Step 3: Create keypair ==="
if [ -f ~/.ssh/id_rsa ]; then
    openstack keypair create --public-key ~/.ssh/id_rsa.pub mykey 2>/dev/null || echo "Keypair already exists"
else
    ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
    openstack keypair create --public-key ~/.ssh/id_rsa.pub mykey
fi

echo "=== Step 4: Configure security group ==="
# Add SSH and ICMP rules to default security group
openstack security group rule create --proto tcp --dst-port 22 default 2>/dev/null || echo "SSH rule exists"
openstack security group rule create --proto icmp default 2>/dev/null || echo "ICMP rule exists"

echo "=== Step 5: Get network info ==="
PRIVATE_NET=$(openstack network show private -f value -c id)
echo "Private network: $PRIVATE_NET"

echo "=== Step 6: Create instances ==="
for VM in vm1 vm2 vm3; do
    echo "Creating $VM..."
    openstack server create \
        --flavor ds1G \
        --image "ubuntu-22.04-cloudimg" \
        --key-name mykey \
        --network "$PRIVATE_NET" \
        --wait \
        "$VM" 2>&1 | grep -E "status|name|id" || true
done

echo "=== Step 7: List instances ==="
openstack server list

echo "=== Done ==="
