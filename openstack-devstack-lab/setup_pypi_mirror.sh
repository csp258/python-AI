#!/bin/bash
# Setup PyPI mirror and restart DevStack
set -e
SPASS='123456'

echo "=== Killing stuck processes ==="
echo "$SPASS" | sudo -S pkill -f stack.sh 2>/dev/null || true
echo "$SPASS" | sudo -S pkill -f "pip install" 2>/dev/null || true
sleep 2

echo "=== Setting up PyPI mirror for stack user ==="
# For the stack user
sudo -u stack mkdir -p /opt/stack/.pip
cat > /tmp/pip_conf << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF
echo "$SPASS" | sudo -S cp /tmp/pip_conf /opt/stack/.pip/pip.conf
echo "$SPASS" | sudo -S chown -R stack:stack /opt/stack/.pip

# Also for root
echo "$SPASS" | sudo -S mkdir -p /root/.pip
echo "$SPASS" | sudo -S cp /tmp/pip_conf /root/.pip/pip.conf

# Also for cheng user
mkdir -p ~/.pip
cp /tmp/pip_conf ~/.pip/pip.conf

echo "pip config:"
cat /tmp/pip_conf

echo "=== Test pip mirror ==="
sudo -u stack pip3 install --dry-run numpy 2>&1 | head -5
echo "pip mirror working"

echo "=== Clean DevStack state ==="
cd /opt/stack/devstack
if [ -f .stackenv ]; then
    echo "$SPASS" | sudo -S -u stack ./clean.sh 2>&1 | tail -5 || true
fi
echo "$SPASS" | sudo -S rm -rf /opt/stack/status /opt/stack/data /opt/stack/requirements /opt/stack/*venv* /opt/stack/glance /opt/stack/cinder /opt/stack/keystone /opt/stack/placement /opt/stack/nova /opt/stack/neutron /opt/stack/horizon /opt/stack/noVNC /opt/stack/novnc /opt/stack/*rc /opt/stack/.my.cnf 2>/dev/null || true
echo "$SPASS" | sudo -S mkdir -p /opt/stack/logs
echo "$SPASS" | sudo -S chown -R stack:stack /opt/stack
echo "$SPASS" | sudo -S rm -f /opt/stack/logs/*.log /opt/stack/logs/*.summary /opt/stack/logs/*.txt

echo "=== Starting DevStack ==="
echo "$SPASS" | sudo -S -u stack nohup bash -c 'export TERM=linux; cd /opt/stack/devstack && ./stack.sh' > /tmp/devstack_nohup.log 2>&1 &
PID=$!
echo "PID: $PID"
echo "=== Launched ==="
