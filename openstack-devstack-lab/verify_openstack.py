#!/usr/bin/env python3
"""Verify OpenStack installation."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '192.168.153.128'
USER = 'cheng'
PASS = '123456'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)

def run(cmd, timeout=60):
    print(f"\n>>> {cmd[:120]}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out: print(out.strip())
    if err: print("[E]", err.strip())
    return out, err

# Source openrc and check services
print("=" * 60)
print("SOURCE OPENRC AND VERIFY OPENSTACK")
print("=" * 60)

run('source /opt/stack/devstack/openrc admin admin && openstack service list')
run('source /opt/stack/devstack/openrc admin admin && openstack endpoint list')
run('source /opt/stack/devstack/openrc admin admin && openstack image list')
run('source /opt/stack/devstack/openrc admin admin && openstack flavor list')
run('source /opt/stack/devstack/openrc admin admin && openstack network list')
run('source /opt/stack/devstack/openrc admin admin && openstack hypervisor list')
run('source /opt/stack/devstack/openrc admin admin && openstack catalog list')

# Check system services
print("\n" + "=" * 60)
print("SYSTEMD SERVICES")
print("=" * 60)
run('systemctl list-units --type=service | grep devstack | head -20')

# Check Horizon accessibility
print("\n" + "=" * 60)
print("HORIZON CHECK")
print("=" * 60)
run('curl -s -o /dev/null -w "%{http_code}" http://192.168.153.128/dashboard')

client.close()
print("\nDone!")
