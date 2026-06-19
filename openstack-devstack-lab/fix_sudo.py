#!/usr/bin/env python3
"""Fix sudoers for stack user and restart DevStack."""
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '192.168.153.128'
USER = 'cheng'
PASS = '123456'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)

def run(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print(f">>> {cmd[:80]}")
    if out: print(out.strip())
    if err: print("[E]", err.strip())
    return out, err

# Kill existing stack.sh
run('echo 123456 | sudo -S pkill -f stack.sh 2>/dev/null; sleep 1; echo "killed"')

# Check sudoers for stack
print("\n=== Current sudoers ===")
run('echo 123456 | sudo -S cat /etc/sudoers.d/stack 2>/dev/null || echo "NO FILE"')
run('echo 123456 | sudo -S ls /etc/sudoers.d/')

# Fix sudoers
print("\n=== Fixing sudoers ===")
run('echo "stack ALL=(ALL) NOPASSWD: ALL" | echo 123456 | sudo -S tee /etc/sudoers.d/stack')
run('echo 123456 | sudo -S chmod 440 /etc/sudoers.d/stack')

# Verify stack user can sudo without password
print("\n=== Verify stack sudo ===")
run('sudo -u stack sudo -n echo STACK_SUDO_OK')

# Check local.conf exists
print("\n=== local.conf ===")
run('ls -la /opt/stack/devstack/local.conf')

# Check logs dir
print("\n=== Logs dir ===")
run('ls -la /opt/stack/logs/')

client.close()
