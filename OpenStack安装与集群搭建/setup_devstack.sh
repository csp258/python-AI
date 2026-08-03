#!/bin/bash
set -e
echo "=== DevStack Setup for Ubuntu 22.04 ==="

# Checkout correct branch
cd /opt/stack/devstack
git checkout unmaintained/2023.1

# Verify jammy support
grep SUPPORTED_DISTROS stackrc

echo "=== Branch ready ==="
