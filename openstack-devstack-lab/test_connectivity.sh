#!/bin/bash
SPASS='123456'

echo "=== 1. Test ping to floating IPs ==="
for ip in 172.24.4.186 172.24.4.229 172.24.4.244; do
    ping -c 2 -W 2 $ip && echo "$ip PING OK" || echo "$ip PING FAIL"
done

echo ""
echo "=== 2. Test SSH to floating IPs with password ==="
for ip in 172.24.4.186 172.24.4.229 172.24.4.244; do
    sshpass -p 'openstack' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@$ip "hostname && echo SSH_OK" 2>&1 || echo "$ip SSH FAILED"
done

echo ""
echo "=== 3. Test SSH to floating IPs with key ==="
for ip in 172.24.4.186 172.24.4.229 172.24.4.244; do
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -i /tmp/vm_ssh_key/id_rsa ubuntu@$ip "hostname && echo SSH_OK" 2>&1 || echo "$ip SSH_KEY FAILED"
done

echo ""
echo "=== 4. Try pinging private IPs ==="
for ip in 10.0.0.39 10.0.0.55 10.0.0.17; do
    ping -c 2 -W 2 $ip && echo "$ip PING OK" || echo "$ip PING FAIL"
done

echo ""
echo "=== 5. Check OVN flows ==="
echo "$SPASS" | sudo -S ovs-ofctl dump-flows br-int 2>/dev/null | grep -E "n_packets=[1-9]|dnat|snat" | head -10
