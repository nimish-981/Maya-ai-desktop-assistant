#!/usr/bin/env python3
"""
MAYA // CYBER COMPANION OS — WEB RUNTIME LAUNCHER
Launches Web_maya with full 198 tools, OS automation, neural voice,
and cyberpunk HUD on port 8080.
"""
import sys
import os
import webbrowser
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(str(ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Web_maya.app import run, PORT

def _open_browser():
    time.sleep(1.0)
    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except Exception:
        pass

if __name__ == "__main__":
    threading.Thread(target=_open_browser, daemon=True).start()
    run()
