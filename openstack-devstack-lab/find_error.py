#!/usr/bin/env python3
"""Find the error in DevStack log."""
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
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out: print(out.strip())
    if err: print("[STDERR]", err.strip())
    return out, err

# Search log for errors (grep for Error, error, FAIL, failed, exit, traceback)
print("=== Searching for errors in stack.sh log ===")
run('grep -i -E "error|fail|traceback|fatal|exit|abort|cannot|denied" /opt/stack/logs/stack.sh.log.2026-06-19-100423 2>/dev/null | head -40')

print("\n=== Looking at context around exit 100 ===")
run('grep -B5 "exit 100" /opt/stack/logs/stack.sh.log.2026-06-19-100423 2>/dev/null | head -30')

print("\n=== Last meaningful lines before exit ===")
run('grep -v "tput:" /opt/stack/logs/stack.sh.log.2026-06-19-100423 2>/dev/null | tail -30')

client.close()
