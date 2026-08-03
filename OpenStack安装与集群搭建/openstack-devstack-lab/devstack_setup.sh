#!/bin/bash
# DevStack setup script
set -e

SPASS='123456'
esudo() { echo "$SPASS" | sudo -S "$@" 2>&1; }

echo "=== Step 1: Check tools ==="
echo "git: $(which git)"

echo "=== Step 2: Create stack user ==="
if ! id stack &>/dev/null; then
    esudo useradd -s /bin/bash -d /opt/stack -m stack
    echo "stack ALL=(ALL) NOPASSWD: ALL" | esudo tee /etc/sudoers.d/stack
    echo "stack user created"
else
    echo "stack user exists: $(id stack)"
fi

echo "=== Step 3: Clone DevStack ==="
if [ -f /opt/stack/devstack/stack.sh ]; then
    echo "DevStack already exists"
    cd /opt/stack/devstack
    git log --oneline -1
else
    esudo mkdir -p /opt/stack
    esudo chown stack:stack /opt/stack
    sudo -u stack git clone https://opendev.org/openstack/devstack -b unmaintained/2023.1 /opt/stack/devstack
    echo "DevStack cloned successfully"
fi

echo "=== Step 4: Verify ==="
ls -la /opt/stack/devstack/stack.sh
cd /opt/stack/devstack && git log --oneline -1

echo "=== Setup complete ==="
