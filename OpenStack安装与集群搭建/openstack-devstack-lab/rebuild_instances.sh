#!/bin/bash
# Rebuild instances with password-based SSH access via cloud-init
set -e

source /opt/stack/devstack/openrc admin admin
export OS_PASSWORD=admin123

echo "=== Step 1: Delete existing instances ==="
for VM in vm1 vm2 vm3; do
    echo "Deleting $VM..."
    openstack server delete $VM --wait 2>/dev/null || true
done

# Clean up old floating IPs
for FIP in $(openstack floating ip list -f value -c "Floating IP Address"); do
    openstack floating ip delete $FIP 2>/dev/null || true
done

echo "=== Step 2: Create cloud-init config ==="
cat > /tmp/cloud-init.yaml << 'EOF'
#cloud-config
password: openstack
chpasswd:
  expire: false
ssh_pwauth: true
package_update: true
package_upgrade: false
packages:
  - openssh-server
runcmd:
  - echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
  - systemctl restart ssh
EOF

echo "=== Step 3: Get private network ID ==="
PRIVATE_NET=$(openstack network show private -f value -c id)
echo "Private: $PRIVATE_NET"

echo "=== Step 4: Create new instances with cloud-init ==="
for VM in vm1 vm2 vm3; do
    echo "Creating $VM..."
    openstack server create \
        --flavor ds1G \
        --image "ubuntu-22.04-cloudimg" \
        --key-name mykey \
        --user-data /tmp/cloud-init.yaml \
        --network "$PRIVATE_NET" \
        --wait \
        "$VM" 2>&1 | grep -E "status|name|id" || true
    echo "$VM created"
done

echo "=== Step 5: Assign floating IPs ==="
for VM in vm1 vm2 vm3; do
    FIP=$(openstack floating ip create public -f value -c floating_ip_address)
    openstack server add floating ip $VM $FIP
    echo "$VM: $FIP"
done

echo "=== Step 6: List instances ==="
openstack server list

echo "=== Done ==="
