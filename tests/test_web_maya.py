import sys
import os
import time
import json
import urllib.request
import threading
from pathlib import Path
from http.server import HTTPServer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from Web_maya.app import MayaWebHandler, PORT, assistant_instance

print(f"=== TEST 1: Checking Assistant Initialization ===")
tool_count = len(getattr(assistant_instance, 'tools_map', {})) if assistant_instance else 0
print(f"✅ Assistant loaded successfully! Registered tools: {tool_count}")
assert tool_count > 100, f"Expected >100 tools, got {tool_count}"

# Start web server with proper shutdown control
httpd = HTTPServer(("", PORT), MayaWebHandler)
server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
server_thread.start()
time.sleep(1.5)

try:
    print("\n=== TEST 2: Testing Static File Serving ===")
    with urllib.request.urlopen(f"http://localhost:{PORT}/") as resp:
        content = resp.read().decode('utf-8')
        assert "MAYA // CYBER COMPANION OS" in content
        print(f"✅ GET / served index.html correctly ({len(content)} bytes)")

    with urllib.request.urlopen(f"http://localhost:{PORT}/style.css") as resp:
        content = resp.read().decode('utf-8')
        assert "--color-bg" in content
        print(f"✅ GET /style.css served correctly ({len(content)} bytes)")

    print("\n=== TEST 3: Testing Telemetry Endpoint ===")
    with urllib.request.urlopen(f"http://localhost:{PORT}/api/telemetry") as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"✅ GET /api/telemetry returned: {data}")
        assert data["status"] == "ONLINE"
        assert data["tools_registered"] > 100

    print("\n=== TEST 4: Testing Chat API (Direct Query) ===")
    req = urllib.request.Request(
        f"http://localhost:{PORT}/api/chat",
        data=json.dumps({"prompt": "Hello Maya, tell me one interesting fact about space in 1 sentence."}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print(f"✅ Maya Reply: {res.get('reply')}")
        assert res.get('reply')
        assert "cloud simulation" not in res.get('reply').lower()

    print("\n=== TEST 5: Testing AI Image Generation Tool ===")
    req_img = urllib.request.Request(
        f"http://localhost:{PORT}/api/chat",
        data=json.dumps({"prompt": "Maya, generate an image of a neon cybernetic tiger in synthwave style"}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_img, timeout=40) as resp:
        res_img = json.loads(resp.read().decode('utf-8'))
        print(f"✅ Maya Image Reply: {res_img.get('reply')}")
        print(f"✅ Image URL: {res_img.get('image_url')}")
        assert res_img.get('image_url')

    print("\n🎉 ALL TESTS PASSED WITH 100% PERFECTION!")

finally:
    print("Shutting down test server...")
    httpd.shutdown()
    httpd.server_close()
    print("Server shut down cleanly.")
