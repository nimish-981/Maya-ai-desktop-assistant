import sys
import os
import threading
import time
import psutil
import webview
from core.engine import Assistant

# Ensure UTF-8 output handling on Windows consoles
for stream in (sys.stdout, sys.stderr):
    if stream and hasattr(stream, 'reconfigure'):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

class MayaDesktopBridge:
    def __init__(self):
        self.assistant = None
        self.window = None

    def set_window(self, window):
        self.window = window

    def send_command(self, text):
        """Called from JavaScript when user types a command and presses Enter"""
        if not text or not self.assistant:
            return
        # Run command execution in background thread
        threading.Thread(target=self._exec_command, args=(text,), daemon=True).start()

    def _exec_command(self, text):
        try:
            self._update_state("THINKING", "PROCESSING...")
            self.assistant._process_with_ai(text)
        except Exception as e:
            self._log_terminal(f"Error executing command: {e}", "sys")
        finally:
            self._update_state("IDLE", "STANDBY")

    def trigger_listen(self):
        """Called from JavaScript when user clicks the LISTEN button"""
        if not self.assistant:
            return
        threading.Thread(target=self._manual_listen, daemon=True).start()

    def _manual_listen(self):
        try:
            self._update_state("LISTENING", "LISTENING...")
            self._log_terminal("Listening for your voice...", "sys")
            user_input = self.assistant.voice.listen()
            if user_input:
                self._log_terminal(f"You: {user_input}", "user")
                self._update_state("THINKING", "PROCESSING...")
                self.assistant._process_with_ai(user_input)
            else:
                self._log_terminal("No speech detected.", "sys")
        except Exception as e:
            self._log_terminal(f"Voice error: {e}", "sys")
        finally:
            self._update_state("IDLE", "STANDBY")

    def _update_state(self, state, text=None):
        if not self.window:
            return
        try:
            safe_text = f"'{text}'" if text else "null"
            self.window.evaluate_js(f"window.setMayaState && window.setMayaState('{state}', {safe_text});")
        except Exception:
            pass

    def _log_terminal(self, msg, log_type="sys"):
        if not self.window:
            return
        try:
            safe_msg = msg.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
            self.window.evaluate_js(f"window.addTerminalLog && window.addTerminalLog('{safe_msg}', '{log_type}');")
        except Exception:
            pass


class StdoutInterceptor:
    """Mirrors console prints and translates them into live 3D UI states and logs."""
    def __init__(self, bridge, original_stdout):
        self.bridge = bridge
        self.original_stdout = original_stdout

    def write(self, text):
        if self.original_stdout:
            try:
                self.original_stdout.write(text)
                self.original_stdout.flush()
            except Exception:
                pass

        clean = text.strip()
        if not clean or not self.bridge.window:
            return

        # Pattern match engine states to 3D UI states
        if "Maya:" in clean:
            msg = clean.split("Maya:", 1)[1].strip()
            self.bridge._update_state("SPEAKING", "RESPONDING...")
            self.bridge._log_terminal(f"Maya: {msg}", "sys")
        elif "You said:" in clean:
            user_msg = clean.split("You said:", 1)[1].strip()
            self.bridge._log_terminal(f"You: {user_msg}", "user")
        elif "Executing Tool:" in clean:
            tool = clean.split("Executing Tool:", 1)[1].strip()
            self.bridge._update_state("EXECUTING", f"RUNNING: {tool}")
            self.bridge._log_terminal(f"Executing: {tool}", "sys")
        elif "Listening" in clean:
            self.bridge._update_state("LISTENING", "LISTENING...")
        elif "Processing" in clean or "Thinking" in clean:
            self.bridge._update_state("THINKING", "PROCESSING...")
        elif "SLEEP MODE" in clean or "Waiting for" in clean:
            self.bridge._update_state("IDLE", "STANDBY")
        elif "Neural interface loaded" in clean or "online" in clean.lower():
            self.bridge._update_state("IDLE", "ONLINE")

    def flush(self):
        if self.original_stdout:
            try:
                self.original_stdout.flush()
            except Exception:
                pass


def telemetry_loop(bridge):
    """Pushes live CPU and RAM stats to the desktop UI."""
    while True:
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            if bridge.window:
                bridge.window.evaluate_js(f"window.updateTelemetry && window.updateTelemetry({cpu}, {ram});")
        except Exception:
            pass
        time.sleep(2.0)


def engine_worker(bridge):
    """Initializes and runs the Maya Assistant in the background."""
    time.sleep(1.0)
    try:
        bridge._log_terminal("Booting Maya Core Intelligence...", "sys")
        assistant = Assistant()
        bridge.assistant = assistant
        bridge._log_terminal("MAYA Neural Core Connected & Operational.", "sys")
        assistant.run()
    except Exception as e:
        bridge._log_terminal(f"Engine Exception: {e}", "sys")


def main():
    bridge = MayaDesktopBridge()
    original_stdout = sys.stdout
    sys.stdout = StdoutInterceptor(bridge, original_stdout)

    # Path to web-ui index.html
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ui_path = os.path.join(current_dir, "web-ui", "index.html")

    # Create Native Windows Application Window
    window = webview.create_window(
        title="MAYA · Neural Interface Companion",
        url=ui_path,
        width=1280,
        height=820,
        min_size=(1024, 700),
        resizable=True,
        text_select=False,
        background_color="#030408",
        js_api=bridge
    )
    bridge.set_window(window)

    # Start telemetry & engine worker threads
    threading.Thread(target=telemetry_loop, args=(bridge,), daemon=True).start()
    threading.Thread(target=engine_worker, args=(bridge,), daemon=True).start()

    # Launch desktop application GUI loop
    try:
        webview.start(debug=False)
    finally:
        sys.stdout = original_stdout

if __name__ == "__main__":
    main()
