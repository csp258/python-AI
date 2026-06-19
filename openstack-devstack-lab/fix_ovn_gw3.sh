#!/bin/bash
SPASS='123456'

LRP="lrp-986a0c2f-d175-4791-8ce3-b2d9a2249501"

echo "=== Current SB chassis ==="
echo "$SPASS" | sudo -S ovn-sbctl list chassis | grep -E "_uuid|hostname" | head -10

echo ""
echo "=== Current NB gateway_chassis ==="
echo "$SPASS" | sudo -S ovn-nbctl get logical_router_port $LRP gateway_chassis

echo ""
echo "=== Get correct chassis UUID ==="
CHASSIS=$(echo "$SPASS" | sudo -S ovn-sbctl list chassis | grep -A1 "_uuid" | head -1 | awk '{print $3}')
echo "SB Chassis UUID: $CHASSIS"

echo ""
echo "=== Remove ALL gateway chassis entries ==="
echo "$SPASS" | sudo -S ovn-nbctl clear logical_router_port $LRP gateway_chassis

echo ""
echo "=== Set correct gateway chassis ==="
echo "$SPASS" | sudo -S ovn-nbctl lrp-set-gateway-chassis $LRP $CHASSIS 10

echo ""
echo "=== Verify ==="
echo "$SPASS" | sudo -S ovn-nbctl get logical_router_port $LRP gateway_chassis

echo ""
echo "=== Show full router port ==="
echo "$SPASS" | sudo -S ovn-nbctl list logical_router_port $LRP

echo ""
echo "=== Wait for SB update ==="
sleep 3

echo "=== Check cr-lrp chassis ==="
echo "$SPASS" | sudo -S ovn-sbctl find port_binding logical_port=cr-lrp-986a0c2f-d175-4791-8ce3-b2d9a2249501 | grep -E "chassis|up" | head -4

echo ""
echo "=== Ping test ==="
ping -c 3 -W 1 172.24.4.186 && echo "SUCCESS!" || echo "Still failing..."
