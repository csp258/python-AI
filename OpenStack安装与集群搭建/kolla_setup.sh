#!/bin/bash
set -e

# Copy example configs
cp /usr/local/share/kolla-ansible/etc_examples/kolla/* /etc/kolla/

# Write clean globals.yml
cat > /etc/kolla/globals.yml << 'ENDOFYML'
kolla_base_distro: "ubuntu"
kolla_install_type: "source"
openstack_release: "2023.1"
network_interface: "ens33"
kolla_internal_vip_address: "192.168.153.128"
neutron_external_interface: "ens33"
enable_cinder: "no"
enable_swift: "no"
enable_heat: "no"
nova_compute_virt_type: "qemu"
ENDOFYML

echo "Config written:"
cat /etc/kolla/globals.yml
echo "=== Running prechecks ==="
kolla-ansible prechecks -i /tmp/all-in-one 2>&1 | tail -20
