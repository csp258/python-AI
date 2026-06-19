#!/usr/bin/env python3
"""Check and fix DevStack database library bug."""
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
    print(f"\n>>> {cmd[:120]}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out: print(out.strip())
    if err: print("[E]", err.strip())
    return out, err

# Check the database library around line 135
print("=== database_connection_url function ===")
run('grep -n "database_connection_url" /opt/stack/devstack/lib/database')

# Show lines around 130-145
print("\n=== Lines 125-150 of lib/database ===")
run('sed -n "125,150p" /opt/stack/devstack/lib/database')

# Check if this is a known issue - what does the function look like?
print("\n=== Full database_connection_url_ pattern ===")
run('grep -rn "database_connection_url_" /opt/stack/devstack/lib/')

client.close()
