#!/usr/bin/env python3
"""Clean up VM and prepare for DevStack installation."""
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '192.168.153.128'
USER = 'cheng'
PASS = '123456'

def run(client, cmd, timeout=120, sudo=False):
    """Run command, print output in real-time."""
    if sudo and not cmd.startswith('sudo'):
        cmd = 'sudo ' + cmd
    cmd = 'echo ">>> ' + cmd.replace('"', '\\"')[:80] + '..." 1>&2; ' + cmd
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        print(out)
    if err:
        print("[E]", err)
    return out + err

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
print("=== Connected ===")

# Ask for sudo password once
# Actually paramiko doesn't have a great way to maintain sudo session
# Let's just check what sudo needs

# Step 1: Clean up snaps we don't need
cmds = [
    # Stop and remove Juju controller + LXD
    "echo 'cheng123456' | sudo -S lxc stop juju-897fc1-0 2>/dev/null; echo 'cheng123456' | sudo -S lxc delete juju-897fc1-0 2>/dev/null; echo lxc_cleaned",
    "echo 'cheng123456' | sudo -S snap remove --purge openstack 2>&1 | tail -5",
    "echo 'cheng123456' | sudo -S snap remove --purge juju 2>&1 | tail -5",
    "echo 'cheng123456' | sudo -S snap remove --purge lxd 2>&1 | tail -5",
    # Clean Docker
    "echo 'cheng123456' | sudo -S docker system prune -af 2>&1 | tail -5",
]

for c in cmds:
    run(client, c, timeout=60)

# Check disk space
print("\n=== Disk After Cleanup ===")
run(client, 'df -h /')

# Check what's in /opt
print("\n=== /opt contents ===")
run(client, 'ls -la /opt/')

client.close()
print("\nDone.")
