#!/bin/bash
source /opt/stack/devstack/openrc admin admin
export OS_PASSWORD=admin123

echo "=== Instances ==="
openstack server list

echo ""
echo "=== Floating IPs ==="
openstack floating ip list

echo ""
echo "=== Try ping floating IPs from host ==="
for ip in 172.24.4.186 172.24.4.229 172.24.4.244; do
    ping -c 2 -W 2 $ip && echo "$ip OK" || echo "$ip FAIL"
done

echo ""
echo "=== Check OVN NAT rules ==="
sudo ovn-nbctl list logical_router | head -5
sudo ovn-nbctl lr-nat-list router1 2>/dev/null || sudo ovn-nbctl list nat

echo ""
echo "=== Check br-ex ==="
ip addr show br-ex 2>/dev/null | head -8

echo ""
echo "=== Check if any iptables NAT rules exist ==="
sudo iptables -t nat -L -n 2>/dev/null | head -20
