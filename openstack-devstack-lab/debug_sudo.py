#!/usr/bin/env python3
"""Debug sudo issue in DevStack."""
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
    if err: print("[STDERR]", err.strip())
    return out, err

# Check if stack.sh is still running
run('pgrep -af stack.sh || echo "NOT_RUNNING"')

# Check all log files
run('ls -la /opt/stack/logs/ 2>/dev/null')
run('cat /opt/stack/logs/stack.sh.log.* 2>/dev/null || echo "NO STACK LOG"')
run('tail -20 /tmp/devstack_nohup.log 2>/dev/null || echo "NO NOHUP LOG"')
run('tail -20 /tmp/devstack_script.log 2>/dev/null || echo "NO SCRIPT LOG"')
run('tail -20 /tmp/devstack_output.log 2>/dev/null || echo "NO OUTPUT LOG"')

# Check sudoers configs
run('echo 123456 | sudo -S cat /etc/sudoers.d/stack 2>/dev/null')
run('echo 123456 | sudo -S cat /etc/sudoers.d/50_stack_sh 2>/dev/null')
run('echo 123456 | sudo -S cat /etc/sudoers.d/stack_tty 2>/dev/null')

# Test stack user sudo more thoroughly
run('echo 123456 | sudo -S -u stack bash -c "sudo -n whoami && echo SUDO_OK"')

# Check if there's a sudo lecture or other blocking thing
run('echo 123456 | sudo -S cat /etc/sudoers | grep -v "^#" | grep -v "^$"')

# Check what script command is available
run('which script; script --version 2>&1 || true')

client.close()
