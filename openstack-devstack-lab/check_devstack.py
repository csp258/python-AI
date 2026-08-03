#!/usr/bin/env python3
"""Monitor DevStack installation progress."""
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
    return out, err

# Check if stack.sh is running
out, _ = run('pgrep -f stack.sh || echo "NOT_RUNNING"')
print("stack.sh running:", "YES" if out.strip().isdigit() or "\n" in out else out.strip())

# Check the log - follow the symlink
out, _ = run('tail -30 /opt/stack/logs/stack.sh.log 2>/dev/null || tail -30 /tmp/devstack_nohup.log 2>/dev/null || echo "NO_LOG"')
print("\n=== Latest Log (last 30 lines) ===")
print(out)

# Check for errors in the log
out2, _ = run('grep -i -E "error|fail|traceback|fatal|exit.*100" /opt/stack/logs/stack.sh.log 2>/dev/null | tail -10')
if out2.strip():
    print("\n=== ERRORS Found ===")
    print(out2)

# Check summary
out3, _ = run('cat /opt/stack/logs/stack.sh.log.summary 2>/dev/null')
if out3.strip():
    print("\n=== Summary ===")
    print(out3)

# Check disk
out, _ = run('df -h /')
print("=== Disk ===")
print(out)

client.close()
