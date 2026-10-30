"""
skills/productivity_skills.py

Smart productivity tools — to-do lists, timers, email, finance.
Auto-registered as Groq tools via engine.py.
"""
import os
import time
import threading
from datetime import datetime


# ── TODO LIST ──────────────────────────────────────────────────────────────────
TODO_FILE = os.path.join(os.path.expanduser("~"), "Documents", "MayaTasks.txt")


def _load_todos():
    if not os.path.exists(TODO_FILE):
        return []
    with open(TODO_FILE, encoding="utf-8") as f:
        return [ln.rstrip("\n") for ln in f if ln.strip()]


def _save_todos(lines):
    os.makedirs(os.path.dirname(TODO_FILE), exist_ok=True)
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))


def add_task(task: str) -> str:
    """Adds a new task to the Maya to-do list. Example: task='Buy groceries', 'Study for exam', 'Call mom'."""
    lines = _load_todos()
    entry = f"[ ] {task.strip()}"
    lines.append(entry)
    _save_todos(lines)
    return f"Task added: '{task.strip()}'. You now have {len(lines)} task(s)."


def read_tasks() -> str:
    """Reads and lists all current tasks from the Maya to-do list, showing which are done and which are pending."""
    lines = _load_todos()
    if not lines:
        return "Your to-do list is empty! Add tasks by saying 'add task: buy milk'."
    pending = [l for l in lines if l.startswith("[ ]")]
    done    = [l for l in lines if l.startswith("[x]")]
    result  = f"You have {len(pending)} pending and {len(done)} completed task(s). "
    if pending:
        result += "Pending: " + "; ".join(t[4:] for t in pending[:5])
        if len(pending) > 5:
            result += f" ...and {len(pending)-5} more."
    return result


def complete_task(task: str) -> str:
    """Marks a task as complete/done in the Maya to-do list. Provide the task name or keyword."""
    lines = _load_todos()
    task_lower = task.lower().strip()
    updated = False
    new_lines = []
    for line in lines:
        if not updated and line.startswith("[ ]") and task_lower in line.lower():
            new_lines.append("[x] " + line[4:])
            updated = True
        else:
            new_lines.append(line)
    if updated:
        _save_todos(new_lines)
        return f"Great job! Task marked as done: '{task}'."
    return f"Could not find a pending task matching '{task}'."


def clear_completed_tasks() -> str:
    """Removes all completed (done) tasks from the Maya to-do list, keeping only pending ones."""
    lines = _load_todos()
    pending = [l for l in lines if not l.startswith("[x]")]
    removed = len(lines) - len(pending)
    _save_todos(pending)
    return f"Cleared {removed} completed task(s). {len(pending)} task(s) remain."


# ── TIMERS ─────────────────────────────────────────────────────────────────────

def start_timer(seconds: str, label: str) -> str:
    """Starts a countdown timer for the given number of seconds. A spoken alert fires when it expires.
    Example: seconds='300', label='pasta timer' — alerts after 5 minutes."""
    try:
        import win32com.client, pythoncom
        secs = max(1, int(''.join(filter(str.isdigit, seconds)) or '60'))
        label = label.strip() or "Timer"

        def _fire():
            time.sleep(secs)
            print(f"🔔 TIMER DONE: {label}")
            try:
                pythoncom.CoInitialize()
                sp = win32com.client.Dispatch("SAPI.SpVoice")
                sp.Speak(f"Time's up! {label} is done.")
            except Exception:
                try:
                    import pyttsx3
                    e = pyttsx3.init(); e.say(f"Time's up! {label}"); e.runAndWait()
                except Exception:
                    pass

        threading.Thread(target=_fire, daemon=True).start()
        mins, rem_s = divmod(secs, 60)
        h, m       = divmod(mins, 60)
        if h:
            time_str = f"{h}h {m}m"
        elif mins:
            time_str = f"{mins} minute{'s' if mins > 1 else ''}"
        else:
            time_str = f"{secs} second{'s' if secs > 1 else ''}"
        return f"Timer set! '{label}' will alert in {time_str}."
    except Exception as e:
        return f"Could not start timer: {e}"


def start_pomodoro() -> str:
    """Starts a Pomodoro productivity timer — 25 minutes of focus followed by a 5-minute break alert."""
    def _run():
        time.sleep(25 * 60)
        print("🔔 POMODORO: Focus session complete! Take a 5-minute break.")
        try:
            import win32com.client, pythoncom
            pythoncom.CoInitialize()
            sp = win32com.client.Dispatch("SAPI.SpVoice")
            sp.Speak("Pomodoro complete! Great work. Take a 5-minute break now.")
        except Exception:
            pass
        time.sleep(5 * 60)
        print("🔔 POMODORO: Break over! Time to focus again.")
        try:
            import win32com.client, pythoncom
            pythoncom.CoInitialize()
            sp = win32com.client.Dispatch("SAPI.SpVoice")
            sp.Speak("Break over! Back to work. Starting next Pomodoro.")
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()
    return "Pomodoro started! 25 minutes of focused work. I'll alert you when it's time for a break."


# ── FINANCE ────────────────────────────────────────────────────────────────────

def get_stock_price(symbol: str) -> str:
    """Fetches the current real-time stock price and basic info for any ticker symbol.
    Example: symbol='AAPL', 'TSLA', 'GOOGL', 'RELIANCE.NS' (for Indian stocks)."""
    import urllib.request, json
    try:
        symbol = symbol.upper().strip()
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        meta = data["chart"]["result"][0]["meta"]
        price    = meta.get("regularMarketPrice", "N/A")
        prev     = meta.get("chartPreviousClose", price)
        currency = meta.get("currency", "USD")
        change   = round(float(price) - float(prev), 2) if price != "N/A" else 0
        pct      = round(change / float(prev) * 100, 2) if prev else 0
        direction = "up" if change >= 0 else "down"
        return (f"{symbol}: {price} {currency}, {direction} {abs(change)} "
                f"({abs(pct)}%) from yesterday's close.")
    except Exception as e:
        return f"Could not fetch stock price for '{symbol}'. Error: {e}"


def get_currency_rate(from_currency: str, to_currency: str) -> str:
    """Gets the current exchange rate between two currencies.
    Example: from_currency='USD', to_currency='INR' or 'EUR' to 'GBP'."""
    import urllib.request, json
    try:
        fc = from_currency.upper().strip()
        tc = to_currency.upper().strip()
        url = f"https://api.exchangerate-api.com/v4/latest/{fc}"
        req = urllib.request.Request(url, headers={"User-Agent": "Maya-Assistant/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        rate = data["rates"].get(tc)
        if rate is None:
            return f"Currency code '{tc}' not found."
        return f"1 {fc} = {rate:.4f} {tc} (as of {data.get('date', 'today')})."
    except Exception as e:
        return f"Could not fetch exchange rate: {e}"


# ── EMAIL ──────────────────────────────────────────────────────────────────────

def open_email_client() -> str:
    """Opens the default Windows email client (Outlook, Mail app, Gmail in browser, etc.)."""
    import webbrowser
    try:
        webbrowser.open("mailto:")
        return "Opening email client."
    except Exception:
        webbrowser.open("https://mail.google.com")
        return "Opening Gmail in your browser."


def compose_email(recipient: str, subject: str, body: str) -> str:
    """Opens the default email client with a pre-filled compose window.
    Example: recipient='boss@company.com', subject='Meeting', body='Hi, can we reschedule?'"""
    import urllib.parse, webbrowser
    try:
        mailto = (f"mailto:{recipient}"
                  f"?subject={urllib.parse.quote(subject)}"
                  f"&body={urllib.parse.quote(body)}")
        webbrowser.open(mailto)
        return f"Email compose window opened for {recipient}."
    except Exception as e:
        return f"Could not open email compose: {e}"


# ── UTILITY ────────────────────────────────────────────────────────────────────

def word_count(text: str) -> str:
    """Counts the number of words, characters, and sentences in a given text."""
    words     = len(text.split())
    chars     = len(text)
    chars_nsp = len(text.replace(" ", ""))
    sentences = text.count('.') + text.count('!') + text.count('?')
    return (f"Analysis: {words} words, {chars} characters "
            f"({chars_nsp} without spaces), ~{sentences} sentence(s).")


def generate_password(length: str, complexity: str) -> str:
    """Generates a strong random password. length example: '16'. complexity: 'simple', 'medium', or 'strong'."""
    import random, string
    try:
        n = max(6, min(64, int(''.join(filter(str.isdigit, length)) or '16')))
        comp = complexity.lower().strip()
        if comp == "simple":
            chars = string.ascii_letters + string.digits
        elif comp == "medium":
            chars = string.ascii_letters + string.digits + "!@#$%"
        else:  # strong
            chars = string.ascii_letters + string.digits + string.punctuation
        # Ensure at least one of each required type
        pwd = (random.choice(string.ascii_uppercase)
               + random.choice(string.ascii_lowercase)
               + random.choice(string.digits)
               + ''.join(random.choices(chars, k=n-3)))
        pwd_list = list(pwd)
        random.shuffle(pwd_list)
        password = ''.join(pwd_list)
        return f"Generated password: {password}"
    except Exception as e:
        return f"Password generation failed: {e}"


def get_public_ip() -> str:
    """Fetches the public IP address of this computer from the internet."""
    import urllib.request
    try:
        with urllib.request.urlopen("https://api.ipify.org?format=json", timeout=5) as r:
            import json
            data = json.loads(r.read().decode())
        return f"Your public IP address is: {data['ip']}"
    except Exception as e:
        return f"Could not fetch public IP: {e}"
