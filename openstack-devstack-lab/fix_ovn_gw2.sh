#!/bin/bash
SPASS='123456'

LRP="lrp-986a0c2f-d175-4791-8ce3-b2d9a2249501"
CHASSIS="f37794b3-9386-4d81-8d7e-9dedd576485c"

echo "=== Remove all gateway chassis entries ==="
echo "$SPASS" | sudo -S ovn-nbctl lrp-del-gateway-chassis $LRP $CHASSIS 2>/dev/null || true
sleep 1

echo "=== Clear gateway chassis list completely ==="
echo "$SPASS" | sudo -S ovn-nbctl clear logical_router_port $LRP gateway_chassis 2>/dev/null || true
sleep 1

echo "=== Re-add gateway chassis with priority 10 ==="
echo "$SPASS" | sudo -S ovn-nbctl lrp-set-gateway-chassis $LRP $CHASSIS 10 2>&1

echo ""
echo "=== Verify gateway chassis ==="
echo "$SPASS" | sudo -S ovn-nbctl get logical_router_port $LRP gateway_chassis 2>&1

echo ""
echo "=== Wait for ovn-controller to create cr-lrp ==="
sleep 3

echo "=== Check SB for cr-lrp ==="
echo "$SPASS" | sudo -S ovn-sbctl find port_binding logical_port=cr-lrp-986a0c2f-d175-4791-8ce3-b2d9a2249501 2>/dev/null || echo "cr-lrp NOT FOUND"

echo ""
echo "=== Check all SB port bindings ==="
echo "$SPASS" | sudo -S ovn-sbctl list port_binding | grep -E "logical_port|chassis" | head -20

echo ""
echo "=== Try ping ==="
ping -c 2 -W 2 172.24.4.186 && echo "OK" || echo "FAIL"
ping -c 2 -W 2 172.24.4.229 && echo "OK" || echo "FAIL"
