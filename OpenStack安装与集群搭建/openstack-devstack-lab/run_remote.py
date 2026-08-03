#!/usr/bin/env python3
"""Upload and run a script on VM via SFTP+SSH, streaming output."""
import sys
import os
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '**********'
USER = 'cheng'
PASS = '**********'

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_remote.py <local_script.sh>")
        sys.exit(1)

    local_script = sys.argv[1]
    remote_path = '/home/cheng/_remote_script.sh'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=15)
    print(f"Connected to {HOST}")

    # Upload script
    sftp = client.open_sftp()
    sftp.put(local_script, remote_path)
    sftp.close()
    print(f"Uploaded {local_script} -> {remote_path}")

    # Make executable
    client.exec_command(f'chmod +x {remote_path}')

    # Run with real-time output streaming
    print("=== Running script ===")
    transport = client.get_transport()
    channel = transport.open_session()
    channel.exec_command(f'bash {remote_path}')

    while True:
        if channel.recv_ready():
            data = channel.recv(4096)
            if data:
                sys.stdout.write(data.decode('utf-8', errors='replace'))
                sys.stdout.flush()
        if channel.recv_stderr_ready():
            data = channel.recv_stderr(4096)
            if data:
                sys.stderr.write(data.decode('utf-8', errors='replace'))
                sys.stderr.flush()
        if channel.exit_status_ready():
            break
        time.sleep(0.1)

    exit_code = channel.recv_exit_status()
    print(f"\n=== Exit code: {exit_code} ===")
    client.close()

if __name__ == '__main__':
    main()
