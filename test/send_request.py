"""
Fire the sample payload at a running local server
Usage:
    python test/send_request.py            # defaults to localhost:8080
    "https://blender-api-652963436516.us-central1.run.app/render"

    python test/send_request.py http://127.0.0.1:9000
"""
import sys, json, pprint, requests, pathlib

endpoint = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080/render"
payload  = json.loads(pathlib.Path(__file__).with_name("payload.json").read_text())

print(f"POST → {endpoint}")
resp = requests.post(endpoint, json=payload, timeout=60000)

print("Status:", resp.status_code)
try:
    pprint.pp(resp.json(), width=120)
except ValueError:
    print(resp.text)
