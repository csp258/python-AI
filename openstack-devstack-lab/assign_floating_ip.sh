#!/bin/bash
# Assign floating IPs to instances
source /opt/stack/devstack/openrc admin admin
export OS_PASSWORD=admin123

echo "=== Public network info ==="
openstack network list
openstack subnet list

echo "=== Assign floating IPs ==="
for VM in vm1 vm2 vm3; do
    # Create floating IP on public network
    FIP=$(openstack floating ip create public -f value -c floating_ip_address)
    echo "Created FIP $FIP for $VM"

    # Assign to instance
    openstack server add floating ip $VM $FIP
    echo "$VM FIP: $FIP"
done

echo "=== Final instance list ==="
openstack server list
