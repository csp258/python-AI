"""Quick API integration test"""
import sys, os, time, json, threading
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn

def start_server():
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, log_level="error")

t = threading.Thread(target=start_server, daemon=True)
t.start()
time.sleep(3)

try:
    r = urllib.request.urlopen("http://127.0.0.1:8000/api/health")
    print("Health:", json.loads(r.read()))

    data = json.dumps({"username": "admin", "password": "123456"}).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/auth/login",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    r = urllib.request.urlopen(req)
    resp = json.loads(r.read())
    print(f"Login OK - User: {resp['user']['username']}, Admin: {resp['user']['is_admin']}")
    print("All API tests passed!")
except Exception as e:
    print(f"Test failed: {e}")
