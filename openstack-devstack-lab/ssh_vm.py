#!/usr/bin/env python3
"""SSH to VM and execute commands, printing output."""
import sys
import traceback

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

try:
    import paramiko
except ImportError:
    print("paramiko not installed, trying pip install...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'paramiko'])
    import paramiko

HOST = '**********'
USER = 'cheng'
PASS = '**********'

def run_cmd(client, cmd, timeout=60):
    """Run a command and return stdout, stderr."""
    print(f"\n>>> {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        print(out)
    if err:
        print("[STDERR]", err)
    return out, err

def main():
    print(f"Connecting to {HOST} as {USER}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(HOST, username=USER, password=PASS, timeout=15)
        print("Connected!")

        # Basic info
        run_cmd(client, 'hostname')
        run_cmd(client, 'df -h /')
        run_cmd(client, 'free -h | head -3')
        run_cmd(client, 'ls -la /opt/stack/ 2>/dev/null || echo "NO /opt/stack"')
        run_cmd(client, 'docker ps -q 2>/dev/null | wc -l')
        run_cmd(client, 'pgrep -af stack.sh || echo "no stack.sh running"')

        cmd = sys.argv[1] if len(sys.argv) > 1 else None
        if cmd:
            run_cmd(client, cmd)

        client.close()
        print("\nDone.")
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
