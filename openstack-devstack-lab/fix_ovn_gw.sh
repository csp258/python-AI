#!/bin/bash
SPASS='123456'

echo "=== Fix 1: Reset gateway chassis (remove duplicate) ==="
echo "$SPASS" | sudo -S ovn-nbctl lrp-del-gateway-chassis lrp-986a0c2f-d175-4791-8ce3-b2d9a2249501 f37794b3-9386-4d81-8d7e-9dedd576485c 2>/dev/null || true
echo "$SPASS" | sudo -S ovn-nbctl lrp-del-gateway-chassis lrp-986a0c2f-d175-4791-8ce3-b2d9a2249501 f37794b3-9386-4d81-8d7e-9dedd576485c 2>/dev/null || true
echo "$SPASS" | sudo -S ovn-nbctl lrp-add-gateway-chassis lrp-986a0c2f-d175-4791-8ce3-b2d9a2249501 f37794b3-9386-4d81-8d7e-9dedd576485c 10

echo "=== Fix 2: Check gateway chassis now ==="
echo "$SPASS" | sudo -S ovn-nbctl show | grep -A5 "lrp-986a0c2f"

echo ""
echo "=== Fix 3: Ensure chassis redirect port exists in SB ==="
echo "$SPASS" | sudo -S ovn-sbctl find port_binding logical_port=cr-lrp-986a0c2f-d175-4791-8ce3-b2d9a2249501 2>/dev/null | head -10

echo ""
echo "=== Fix 4: Try ping again ==="
for ip in 172.24.4.186 172.24.4.229 172.24.4.244; do
    ping -c 2 -W 2 $ip && echo "$ip OK" || echo "$ip FAIL"
done

echo ""
echo "=== Check ARP ==="
arp -n | grep 172.24.4
