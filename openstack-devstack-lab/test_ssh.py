#!/usr/bin/env python3
"""Test SSH to instances and configure cluster."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '192.168.153.128'
USER = 'cheng'
PASS = '123456'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)

def run(cmd, timeout=30):
    print(f"\n>>> {cmd[:100]}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out: print(out.strip())
    if err: print("[E]", err.strip())
    return out, err

# Check if floating IPs are reachable from host
print("=== Test connectivity to floating IPs ===")
for ip in ['172.24.4.186', '172.24.4.229', '172.24.4.244']:
    run(f'ping -c 2 -W 2 {ip}')

# Check routing
print("\n=== Routing table ===")
run('ip route | head -10')

# Check NAT rules for floating IPs
print("\n=== iptables NAT rules ===")
run('echo 123456 | sudo -S iptables -t nat -L -n | head -20')

# Check OVN/OVS setup
print("\n=== br-ex interface ===")
run('ip addr show br-ex 2>/dev/null || echo "no br-ex"')

# Try SSH to instances with the stack user key
print("\n=== Try SSH to vm1 (172.24.4.186) ===")
run('ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i ~/.ssh/id_rsa ubuntu@172.24.4.186 "hostname && echo SSH_OK" 2>&1 || echo "SSH_FAILED"')

client.close()
