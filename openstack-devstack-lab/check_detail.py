#!/usr/bin/env python3
"""Detailed check of DevStack status."""
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

# Check if stack.sh is running
run('pgrep -f "stack.sh" | head -5')
run('ps aux | grep stack.sh | grep -v grep')

# Check log files
run('ls -lt /opt/stack/logs/')
run('cat /opt/stack/logs/stack.sh.log.summary 2>/dev/null')

# Check nohup log
run('tail -10 /tmp/devstack_nohup.log 2>/dev/null || echo "no file"')

# Check if sudo is the issue - test stack user sudo in different contexts
run('echo 123456 | sudo -S -u stack bash -c "TERM=linux sudo -n echo SUDO_OK"')

# Try with ssh -tt equivalent
run('echo 123456 | sudo -S -u stack script -q -c "sudo -n echo SUDO_SCRIPT_OK" /dev/null')

# Check /tmp/devstack_output.log
run('tail -5 /tmp/devstack_output.log 2>/dev/null || echo "no file"')

client.close()
