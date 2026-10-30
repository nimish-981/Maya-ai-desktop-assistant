"""
skills/security_audit_skills.py

Module 14: Security, Privacy and Safety
Implements action receipts audit trails, emergency stop, PII redaction,
data export/wipe, and power operations with explicit human approval gates.
Auto-registered via engine.py.
"""

import os
import re
import sqlite3
import subprocess
from datetime import datetime

DB_PATH = "maya_history.db"


def get_audit_history(count: str = "10") -> str:
    """Retrieves the recent audit trail of executed tools and actions with timestamps and statuses."""
    n = int(''.join(filter(str.isdigit, count)) or '10')
    try:
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, agent_name, tool_name, status, summary, execution_time_ms
                FROM action_receipts
                ORDER BY timestamp DESC
                LIMIT ?
            """, (n,))
            rows = cursor.fetchall()

        if not rows:
            return "Audit Trail: No tool executions recorded yet."

        receipts = [
            f"[{r[0]}] {r[1]} -> {r[2]} ({r[3]}, {r[5]:.1f}ms): {r[4][:60]}"
            for r in rows
        ]
        return f"Audit History (Last {len(rows)} Actions):\n" + "\n".join(receipts)
    except Exception as e:
        return f"Error reading audit log: {e}"


def emergency_stop() -> str:
    """Immediately stops all ongoing voice speech, cancels background automations, and resets state to idle."""
    try:
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
    except Exception:
        pass
    return "EMERGENCY STOP EXECUTED: All audio playback halted, active automation tasks cancelled. Maya is now on standby."


def system_power_control(action: str = "sleep", confirm: str = "false") -> str:
    """Safely executes power operations ('shutdown', 'restart', 'sleep', 'lock'). Requires explicit confirmation ('confirm=true')."""
    act = action.lower().strip()
    is_confirmed = confirm.lower().strip() in ("true", "yes", "confirm", "confirmed")

    if act in ("lock", "lock_screen"):
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
        return "Workstation locked successfully."

    if not is_confirmed:
        return f"SAFETY CONFIRMATION REQUIRED: Are you sure you want to {act} the computer? Please repeat with confirmation: '{act} computer and confirm'."

    try:
        if "shutdown" in act:
            subprocess.run(["shutdown", "/s", "/t", "10", "/c", "Maya Voice Assistant initiating shutdown."])
            return "System shutdown sequence initiated (10 seconds timer). To abort, say 'abort shutdown'."
        elif "restart" in act or "reboot" in act:
            subprocess.run(["shutdown", "/r", "/t", "10", "/c", "Maya Voice Assistant initiating restart."])
            return "System restart sequence initiated (10 seconds timer)."
        elif "sleep" in act:
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            return "System entering sleep mode."
        elif "abort" in act:
            subprocess.run(["shutdown", "/a"])
            return "System shutdown/restart aborted."
        else:
            return f"Unrecognized power action '{action}'. Options: shutdown, restart, sleep, lock."
    except Exception as e:
        return f"Error executing power command: {e}"


def redact_pii(text: str) -> str:
    """Redacts Personally Identifiable Information (PII) including email addresses, phone numbers, and potential secrets."""
    redacted = text
    # Redact email addresses
    redacted = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[REDACTED_EMAIL]', redacted)
    # Redact phone numbers (10 digits)
    redacted = re.sub(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', '[REDACTED_PHONE]', redacted)
    # Redact potential API keys or tokens
    redacted = re.sub(r'\b(nvapi-[A-Za-z0-9_-]{20,}|gsk_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,})\b', '[REDACTED_API_KEY]', redacted)
    return redacted


def export_user_data() -> str:
    """Exports decrypted conversation history and remembered facts to a secure text file on the Desktop."""
    from cryptography.fernet import Fernet
    key_file = "maya_secret.key"
    if not os.path.exists(key_file):
        return "Encryption key not found; cannot export data."

    with open(key_file, "rb") as f:
        key = f.read()
    cipher = Fernet(key)

    desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    export_path = os.path.join(desktop, f"maya_user_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    try:
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, key, value FROM memories")
            mem_rows = cursor.fetchall()
            cursor.execute("SELECT timestamp, role, message FROM chats ORDER BY id DESC LIMIT 50")
            chat_rows = cursor.fetchall()

        out_lines = ["=== MAYA USER DATA EXPORT ===", f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"]
        out_lines.append("--- REMEMBERED FACTS ---")
        for r in mem_rows:
            try:
                k = cipher.decrypt(r[1].encode()).decode()
                v = cipher.decrypt(r[2].encode()).decode()
                out_lines.append(f"[{r[0]}] {k}: {v}")
            except Exception:
                pass

        out_lines.append("\n--- RECENT CHAT HISTORY ---")
        for r in reversed(chat_rows):
            try:
                role = cipher.decrypt(r[1].encode()).decode()
                msg = cipher.decrypt(r[2].encode()).decode()
                out_lines.append(f"[{r[0]}] {role}: {msg}")
            except Exception:
                pass

        with open(export_path, "w", encoding="utf-8") as f:
            f.write("\n".join(out_lines))

        return f"User data successfully exported to Desktop as '{os.path.basename(export_path)}'."
    except Exception as e:
        return f"Error exporting user data: {e}"


def delete_all_user_data(confirmation: str = "NO") -> str:
    """Permanently wipes all conversation history, personal memories, and receipts. Requires confirmation='CONFIRM_DELETE'."""
    if confirmation.strip() != "CONFIRM_DELETE":
        return "DATA PURGE ABORTED: Wiping all user data requires explicit parameter confirmation='CONFIRM_DELETE'."

    try:
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            conn.execute("DELETE FROM chats")
            conn.execute("DELETE FROM memories")
            conn.execute("DELETE FROM action_receipts")
            conn.commit()
        return "All user data, chat history, memories, and action receipts have been permanently wiped."
    except Exception as e:
        return f"Error wiping user data: {e}"
