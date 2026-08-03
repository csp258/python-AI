#!/bin/bash
SPASS='123456'

echo "=== OVN NAT rules ==="
echo "$SPASS" | sudo -S ovn-nbctl lr-nat-list router1 2>/dev/null || echo "$SPASS" | sudo -S ovn-nbctl list nat

echo ""
echo "=== OVN Logical Switch Ports ==="
echo "$SPASS" | sudo -S ovn-nbctl show | head -60

echo ""
echo "=== OVN SB chassis ==="
echo "$SPASS" | sudo -S ovn-sbctl show 2>/dev/null | head -40

echo ""
echo "=== IP route ==="
ip route

echo ""
echo "=== ARP check ==="
arp -n | grep 172.24.4

echo ""
echo "=== Test SSH to instance IP ==="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i ~/.ssh/id_rsa ubuntu@172.24.4.186 "hostname" 2>&1 || echo "SSH to 172.24.4.186 FAILED"
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i ~/.ssh/id_rsa ubuntu@10.0.0.39 "hostname" 2>&1 || echo "SSH to 10.0.0.39 FAILED"
