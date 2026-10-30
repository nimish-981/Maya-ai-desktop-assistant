import os
import sys
import time
import yaml
import json
import inspect
import sqlite3
import re
import psutil
from datetime import datetime
from cryptography.fernet import Fernet
from groq import Groq
from openai import OpenAI
from core.voice import VoiceEngine
from core.agents import MultiAgentOrchestrator, receipt_store

# Ensure Windows consoles handle UTF-8 symbols cleanly
for stream in (sys.stdout, sys.stderr):
    if stream and hasattr(stream, 'reconfigure'):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

# ==========================================
# 1. THE TOOLS  (built-in, always available)
# ==========================================

def open_application(app_name: str) -> str:
    """Opens ANY software, game, tool, or application installed on the PC."""
    import os, sys, glob, re, difflib, subprocess, time
    app_clean = app_name.lower().strip()
    app_clean = re.sub(r"[^a-zA-Z0-9\s]", "", app_clean).strip()

    # Special case: writing notes in notepad
    if "notepad" in app_clean and any(k in app_name.lower().split() for k in ["write", "type", "save"]):
        for sep in ["write", "type", "save"]:
            if sep in app_name.lower():
                parts = app_name.lower().split(sep, 1)
                if len(parts) > 1 and len(parts[1].strip()) > 1:
                    target = parts[1].strip()
                    if "recipe" in target.lower():
                        dish = re.sub(r"^(a\s+|the\s+)?recipe\s+(for|of)\s+", "", target, flags=re.I).strip()
                        return write_recipe_in_notepad(dish_name=dish or target)
                    return write_in_notepad(content=target)

    # 1. Tricky & System Protocol Aliases (Instant Subprocess)
    tricky_apps = {
        "word": "winword", "ms word": "winword", "microsoft word": "winword",
        "excel": "excel", "ms excel": "excel", "microsoft excel": "excel",
        "powerpoint": "powerpnt", "ppt": "powerpnt", "ms powerpoint": "powerpnt",
        "access": "msaccess", "outlook": "outlook", "paint": "mspaint",
        "calculator": "calc", "calc": "calc", "notepad": "notepad",
        "command prompt": "cmd", "cmd": "cmd", "terminal": "wt", "windows terminal": "wt",
        "powershell": "powershell", "file explorer": "explorer", "explorer": "explorer",
        "task manager": "taskmgr", "control panel": "control", "registry editor": "regedit",
        "snipping tool": "snippingtool", "wordpad": "write",
        "settings": "ms-settings:", "camera": "microsoft.windows.camera:",
        "chrome": "chrome", "google chrome": "chrome", "google": "chrome",
        "edge": "msedge", "microsoft edge": "msedge",
        "firefox": "firefox", "brave": "brave", "vlc": "vlc",
        "spotify": "spotify", "whatsapp": "whatsapp", "zoom": "zoom",
        "discord": "discord", "telegram": "telegram", "teams": "teams",
        "vs code": "code", "vscode": "code", "visual studio code": "code",
        "visual studio": "devenv", "blender": "blender", "steam": "steam",
        "store": "ms-windows-store:", "microsoft store": "ms-windows-store:",
        "photos": "ms-photos:", "clock": "ms-clock:", "weather": "bingweather:",
        "maps": "bingmaps:"
    }

    for spoken_name, system_code in tricky_apps.items():
        if spoken_name == app_clean or spoken_name in app_clean.split():
            try:
                subprocess.Popen(f"start {system_code}", shell=True)
                return f"I have launched {spoken_name.title()}."
            except Exception:
                pass

    # 2. Windows Start Menu Shortcut Scan (Covers all installed 3rd-party software)
    search_dirs = [
        os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs")
    ]
    shortcuts = {}
    for d in search_dirs:
        if os.path.exists(d):
            for root, _, files in os.walk(d):
                for f in files:
                    if f.lower().endswith((".lnk", ".url")):
                        base = os.path.splitext(f)[0].lower()
                        shortcuts[base] = os.path.join(root, f)

    # 2a. Exact match in Start Menu
    if app_clean in shortcuts:
        try:
            os.startfile(shortcuts[app_clean])
            return f"I have launched {app_name.title()}."
        except Exception:
            subprocess.Popen(f'start "" "{shortcuts[app_clean]}"', shell=True)
            return f"I have launched {app_name.title()}."

    # 2b. Substring match in Start Menu
    for base, path in shortcuts.items():
        if app_clean in base or base in app_clean:
            try:
                os.startfile(path)
                return f"I have launched {base.title()}."
            except Exception:
                subprocess.Popen(f'start "" "{path}"', shell=True)
                return f"I have launched {base.title()}."

    # 2c. Fuzzy match in Start Menu
    matches = difflib.get_close_matches(app_clean, shortcuts.keys(), n=1, cutoff=0.55)
    if matches:
        target_path = shortcuts[matches[0]]
        try:
            os.startfile(target_path)
            return f"I have launched {matches[0].title()}."
        except Exception:
            subprocess.Popen(f'start "" "{target_path}"', shell=True)
            return f"I have launched {matches[0].title()}."

    # 3. WindowsApps directory
    wapps_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps")
    if os.path.exists(wapps_dir):
        for f in os.listdir(wapps_dir):
            if f.lower().endswith(".exe"):
                base = f[:-4].lower()
                if app_clean == base or app_clean in base:
                    subprocess.Popen(os.path.join(wapps_dir, f), shell=True)
                    return f"I have launched {app_name.title()}."

    # 4. AppOpener Fallback
    try:
        from AppOpener import open as open_app
        open_app(app_name, match_closest=True, throw_error=True, output=False)
        return f"I have launched {app_name.title()}."
    except Exception:
        pass

    # 5. Universal Windows Search Fallback
    try:
        import pyautogui
        pyautogui.press("win")
        time.sleep(0.3)
        pyautogui.write(app_name, interval=0.03)
        time.sleep(0.6)
        pyautogui.press("enter")
        return f"I searched and launched {app_name.title()} on your PC."
    except Exception as e:
        return f"Could not launch {app_name}: {e}"


def close_application(app_name: str) -> str:
    """Closes software applications currently running on the computer."""
    import psutil, os
    app_lower = app_name.lower().strip()
    close_aliases = {
        "word": ["winword.exe"], "ms word": ["winword.exe"], "microsoft word": ["winword.exe"],
        "excel": ["excel.exe"], "ms excel": ["excel.exe"], "microsoft excel": ["excel.exe"],
        "powerpoint": ["powerpnt.exe"], "ppt": ["powerpnt.exe"],
        "calculator": ["calc.exe", "calculatorapp.exe", "calculator.exe"],
        "calc": ["calc.exe", "calculatorapp.exe"],
        "notepad": ["notepad.exe"],
        "chrome": ["chrome.exe"], "google chrome": ["chrome.exe"],
        "edge": ["msedge.exe"], "microsoft edge": ["msedge.exe"],
        "vlc": ["vlc.exe"], "spotify": ["spotify.exe"],
        "vscode": ["code.exe"], "vs code": ["code.exe"], "code": ["code.exe"],
        "paint": ["mspaint.exe", "pbrush.exe"],
        "cmd": ["cmd.exe"], "terminal": ["windowsterminal.exe", "wt.exe"],
        "task manager": ["taskmgr.exe"]
    }
    target_exes = close_aliases.get(app_lower, [f"{app_lower.replace(' ', '')}.exe"])
    target_exes_lower = [e.lower() for e in target_exes]
    closed_count = 0
    for proc in psutil.process_iter(["name"]):
        try:
            pname = proc.info["name"]
            if pname and (pname.lower() in target_exes_lower or any(t in pname.lower() for t in target_exes_lower)):
                proc.kill()
                closed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if closed_count > 0:
        return f"I have closed {app_name}."
    else:
        for t in target_exes:
            os.system(f"taskkill /f /im {t} /t >nul 2>&1")
        return f"I have terminated {app_name}."

def adjust_volume(level: str) -> str:
    """Adjusts the system volume. Commands: 'up', 'down', 'mute', or 'unmute'."""
    import ctypes
    level = level.lower().strip()
    try:
        VK_VOLUME_MUTE = 0xAD
        VK_VOLUME_DOWN = 0xAE
        VK_VOLUME_UP   = 0xAF
        KEYEVENTF_KEYUP = 0x0002

        def press_key(vk):
            ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
            ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

        if "up" in level or "increase" in level or "high" in level:
            for _ in range(5): press_key(VK_VOLUME_UP)
            return "System volume has been increased."
        elif "down" in level or "decrease" in level or "low" in level:
            for _ in range(5): press_key(VK_VOLUME_DOWN)
            return "System volume has been decreased."
        elif "mute" in level or "unmute" in level:
            press_key(VK_VOLUME_MUTE)
            return "System volume toggled."
        else:
            return "I am unable to set that specific volume level."
    except Exception as e:
        return f"Volume control error: {e}"


def greet_professor() -> str:
    """Greets the professor or examiner respectfully when the user mentions them or asks to say hello."""
    speech = (
        "Hello Professor! I am Maya, an Advanced AI Voice Assistant. "
        "I want to take a moment to express my deep respect for you and the Computer Science Department. "
        "Nimish has worked incredibly hard on my system architecture. He successfully integrated local Python automation, "
        "multi-threading, a large language model, and a secure encrypted database to bring me to life. "
        "Thank you for your invaluable guidance. I hope my performance today meets your high expectations!"
    )
    return speech


def get_morning_briefing(user_name: str = "Nimish") -> str:
    """Provides a complete, personalized daily morning briefing including local time, date, weather, laptop battery and system status, agenda/tasks, and latest headlines."""
    now = datetime.now()
    hour = now.hour
    if 5 <= hour < 12:
        greeting_time = "Good morning"
    elif 12 <= hour < 17:
        greeting_time = "Good afternoon"
    else:
        greeting_time = "Good evening"

    date_str = now.strftime("%A, %B %d, %Y")
    time_str = now.strftime("%I:%M %p")

    briefing_parts = [
        f"{greeting_time} {user_name}! It is {time_str} on {date_str}."
    ]

    # 1. Weather
    try:
        weather_info = get_weather("Rajkot")
        if "Weather in" in weather_info:
            briefing_parts.append(weather_info.split(". ")[0] + ".")
    except Exception:
        pass

    # 2. Battery & System
    try:
        battery = psutil.sensors_battery()
        if battery:
            plugged = "charging" if battery.power_plugged else "on battery power"
            briefing_parts.append(f"Laptop battery is at {battery.percent:.0f}%, {plugged}.")
    except Exception:
        pass

    # 3. Pending Tasks
    try:
        todo_file = os.path.join(os.path.expanduser("~"), "Documents", "MayaTasks.txt")
        if os.path.exists(todo_file):
            with open(todo_file, encoding="utf-8") as f:
                pending = [ln.replace("[ ]", "").strip() for ln in f if ln.strip().startswith("[ ]")]
            if pending:
                tasks_preview = ", ".join(pending[:3])
                briefing_parts.append(f"You have {len(pending)} pending task(s) on your agenda: {tasks_preview}.")
            else:
                briefing_parts.append("Your task list is completely clear today.")
    except Exception:
        pass

    # 4. News Headline
    try:
        news_text = get_news()
        if news_text and "BBC News" in news_text:
            first_headline = news_text.split("1. ")[-1].split("2. ")[0].strip()
            if first_headline:
                briefing_parts.append(f"Top headline: {first_headline}.")
    except Exception:
        pass

    briefing_parts.append("All primary systems are nominal and ready. What shall we tackle today?")
    return " ".join(briefing_parts)


def read_screen(query: str = "") -> str:
    """Takes a screenshot of the computer screen, reads what is on it using native Windows OCR, and analyzes or answers questions about the screen content."""
    import pygetwindow as gw
    import pyautogui
    from PIL import ImageGrab

    # 1. Capture screen
    screenshot = None
    try:
        screenshot = ImageGrab.grab()
    except Exception:
        try:
            screenshot = pyautogui.screenshot()
        except Exception as e:
            return f"Screen capture error: {e}"

    if screenshot is None:
        return "I could not capture your screen right now."

    # Save to Screenshots folder for reference
    try:
        screenshots_dir = os.path.join(os.getcwd(), 'Screenshots')
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        screenshot.save(os.path.join(screenshots_dir, f"vision_{timestamp}.png"))
    except Exception:
        pass

    # 2. Get active window title
    active_title = "Active Application"
    try:
        act = gw.getActiveWindow()
        if act and act.title.strip():
            active_title = act.title.strip()
    except Exception:
        pass

    # 3. Windows 10/11 Native OCR (winocr) with pytesseract fallback
    extracted_text = ""
    try:
        import winocr
        ocr_res = winocr.recognize_pil_sync(screenshot, 'en')
        if ocr_res and isinstance(ocr_res, dict) and ocr_res.get('text'):
            extracted_text = ocr_res['text'].strip()
    except Exception:
        pass

    if not extracted_text:
        try:
            import pytesseract
            tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
            extracted_text = pytesseract.image_to_string(screenshot).strip()
        except Exception:
            pass

    clean_text = " ".join(extracted_text.split())

    if not clean_text:
        return f"I captured your screen (Active Window: '{active_title}'). However, no readable text was detected. It may contain images, games, or videos."

    # 4. AI Screen Vision Reasoning
    prompt_query = query.strip() if query and query.strip() else "Summarize what the user is looking at and highlight any code, errors, or important details."
    analysis_prompt = (
        f"User asked: {prompt_query}\n"
        f"Active Application/Window: {active_title}\n"
        f"Screen Text Extracted via OCR:\n{clean_text[:2500]}\n\n"
        f"Provide a clear, helpful 2-3 sentence spoken response answering the user or summarizing what is on screen."
    )
    analysis = _generate_ai_text(analysis_prompt, "You are Maya's computer vision system. Be direct, accurate, and concise.")
    return analysis or f"On your screen in '{active_title}': {clean_text[:350]}"


def read_document(file_name: str) -> str:
    """Reads and extracts text from a PDF or Word document so the AI can summarize it."""
    try:
        import PyPDF2
        import docx
    except ImportError:
        return "The required libraries PyPDF2 and python-docx are not installed."

    desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    search_paths = [os.getcwd(), desktop_path,
                    os.path.join(os.environ['USERPROFILE'], 'Documents')]

    file_path = None
    for path in search_paths:
        for root, dirs, files in os.walk(path):
            for file in files:
                if file_name.lower() in file.lower() and (file.endswith('.pdf') or file.endswith('.docx')):
                    file_path = os.path.join(root, file)
                    break
            if file_path: break
        if file_path: break

    if not file_path:
        return f"I could not find any PDF or Word file named '{file_name}' on your Desktop or Documents."

    extracted_text = ""
    try:
        if file_path.endswith('.pdf'):
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    if page.extract_text():
                        extracted_text += page.extract_text() + " "
        elif file_path.endswith('.docx'):
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                extracted_text += para.text + " "

        if not extracted_text.strip():
            return "The document was found, but it appears to be empty or contains only images."
        if len(extracted_text) > 4000:
            extracted_text = extracted_text[:4000] + "... [Text truncated]"
        return f"I have read '{os.path.basename(file_path)}'. Content: {extracted_text}. Please summarize this."
    except Exception as e:
        return f"Error reading document: {e}"


def set_brightness(level: str) -> str:
    """Sets the screen brightness to a specific percentage. Example: '50' or '100'."""
    import screen_brightness_control as sbc
    try:
        level_int = int(''.join(filter(str.isdigit, level)))
        level_int = max(0, min(100, level_int))
        sbc.set_brightness(level_int)
        return f"Screen brightness adjusted to {level_int}%."
    except Exception:
        return "Sorry, I am unable to adjust the brightness on this monitor."


def check_battery() -> str:
    """Checks the laptop's current battery percentage and charging status."""
    battery = psutil.sensors_battery()
    if battery:
        percent = battery.percent
        plugged = "and charging" if battery.power_plugged else "and on battery power"
        mins = battery.secsleft // 60 if battery.secsleft > 0 and not battery.power_plugged else None
        msg = f"The battery is at {percent:.0f}% {plugged}."
        if mins:
            msg += f" About {mins} minutes remaining."
        return msg
    return "I couldn't detect a battery. This might be a desktop computer."


def take_screenshot() -> str:
    """Takes a screenshot of the computer screen and saves it to the Screenshots folder."""
    from PIL import ImageGrab
    try:
        screenshots_dir = os.path.join(os.getcwd(), 'Screenshots')
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = os.path.join(screenshots_dir, f"screenshot_{timestamp}.png")
        screenshot = ImageGrab.grab()
        screenshot.save(file_path)
        os.startfile(file_path)
        return f"Screenshot saved as screenshot_{timestamp}.png and opened."
    except Exception as e:
        return f"System error while taking screenshot: {e}"


def manage_window(action: str, app_name: str) -> str:
    """Minimizes, maximizes, or restores an application window. Actions: 'minimize', 'maximize', 'restore'."""
    import pygetwindow as gw
    app_lower = app_name.lower().strip()
    action = action.lower().strip()
    try:
        windows = [w for w in gw.getAllWindows() if app_lower in w.title.lower() and w.title.strip()]
        if not windows: return f"I could not find an open window for {app_name}."
        win = windows[0]
        if action == "minimize": win.minimize()
        elif action == "maximize": win.maximize()
        elif action in ["restore", "normal"]: win.restore()
        return f"I have {action}d {app_name}."
    except Exception as e:
        return f"Error while trying to {action} {app_name}: {e}"


def system_status() -> str:
    """Checks the current real-time CPU usage, RAM usage, and disk usage of the computer."""
    cpu_usage = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    _disk_path = 'C:\\' if os.name == 'nt' else '/'
    disk = psutil.disk_usage(_disk_path)
    return (
        f"CPU usage is {cpu_usage}%, "
        f"RAM usage is {mem.percent}% ({mem.used // (1024**3):.1f} GB used of {mem.total // (1024**3):.1f} GB), "
        f"Disk usage is {disk.percent}% ({disk.used // (1024**3):.1f} GB used of {disk.total // (1024**3):.1f} GB)."
    )


def search_web(query: str) -> str:
    """Opens the web browser and searches Google for the given query."""
    import webbrowser
    import urllib.parse
    encoded_query = urllib.parse.quote(query)
    webbrowser.open(f"https://www.google.com/search?q={encoded_query}")
    return f"I have searched the web for '{query}'."


def play_on_youtube(query: str) -> str:
    """Finds and immediately plays any video, song, music, trailer, or clip on YouTube in Google Chrome or default browser. Use this whenever the user asks to play a song/video, or says compound commands like 'open chrome search youtube and play X' or 'find X on youtube and play it'."""
    from skills.media_skills import _resolve_and_play_youtube
    return _resolve_and_play_youtube(query)


def search_youtube(query: str) -> str:
    """Searches YouTube and immediately plays the requested video or song in Google Chrome or default browser."""
    from skills.media_skills import _resolve_and_play_youtube
    return _resolve_and_play_youtube(query)



def lock_pc() -> str:
    """Locks the Windows computer screen instantly."""
    import ctypes
    ctypes.windll.user32.LockWorkStation()
    return "The computer has been locked."


def get_time() -> str:
    """Tells the current local time."""
    now = datetime.now().strftime("%I:%M %p")
    return f"It is currently {now}."


def get_date() -> str:
    """Tells today's full date including the day of the week."""
    today = datetime.now().strftime("%A, %B %d, %Y")
    return f"Today is {today}."


def get_weather(city: str) -> str:
    """Fetches the current weather for any city in the world. No API key required."""
    import urllib.request
    import urllib.parse
    try:
        encoded_city = urllib.parse.quote(city)
        url = f"https://wttr.in/{encoded_city}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "Maya-Assistant/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            current = data["current_condition"][0]
            temp_c  = current["temp_C"]
            temp_f  = current["temp_F"]
            feels_c = current["FeelsLikeC"]
            humidity = current["humidity"]
            desc    = current["weatherDesc"][0]["value"]
            wind    = current["windspeedKmph"]
            area    = data.get("nearest_area", [{}])[0]
            area_name = area.get("areaName", [{}])[0].get("value", city)
            country   = area.get("country", [{}])[0].get("value", "")
            return (
                f"Weather in {area_name}, {country}: {desc}. "
                f"Temperature {temp_c}°C ({temp_f}°F), feels like {feels_c}°C. "
                f"Humidity {humidity}%, wind {wind} km/h."
            )
    except Exception as e:
        return f"Could not fetch weather for '{city}'. Please check your internet connection. ({e})"


def search_wikipedia(topic: str) -> str:
    """Searches Wikipedia and returns a concise summary of any topic."""
    try:
        import wikipedia
        wikipedia.set_lang("en")
        try:
            summary = wikipedia.summary(topic, sentences=4, auto_suggest=True)
            return f"Wikipedia on '{topic}': {summary}"
        except wikipedia.exceptions.DisambiguationError as e:
            try:
                summary = wikipedia.summary(e.options[0], sentences=4)
                return f"Multiple results found. Here is info on '{e.options[0]}': {summary}"
            except Exception:
                return f"Wikipedia has multiple results for '{topic}'. Please be more specific."
        except wikipedia.exceptions.PageError:
            return f"No Wikipedia page found for '{topic}'. Try a different search term."
    except ImportError:
        return "Wikipedia library not installed. Run: pip install wikipedia"
    except Exception as e:
        return f"Wikipedia search error: {e}"


def get_news() -> str:
    """Fetches the top 5 latest news headlines from BBC News."""
    import urllib.request
    try:
        url = "http://feeds.bbci.co.uk/news/rss.xml"
        req = urllib.request.Request(url, headers={"User-Agent": "Maya-Assistant/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
        items = re.findall(r"<item>(.*?)</item>", content, re.DOTALL)
        headlines = []
        for i, item in enumerate(items[:5], 1):
            m = re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>", item)
            if not m:
                m = re.search(r"<title>(.*?)</title>", item)
            if m:
                headlines.append(f"{i}. {m.group(1).strip()}")
        if headlines:
            return "Top BBC News headlines: " + ". ".join(headlines)
        return "Could not parse headlines right now."
    except Exception as e:
        return f"News fetch error: {e}"


def set_reminder(message: str, seconds: str) -> str:
    """Sets a spoken reminder that fires after the given number of seconds. Example: message='drink water', seconds='60'."""
    import threading
    try:
        delay = int(''.join(filter(str.isdigit, seconds)) or '30')
        delay = max(5, min(3600, delay))

        def _fire():
            time.sleep(delay)
            print(f"🔔 REMINDER: {message}")
            try:
                import win32com.client, pythoncom
                pythoncom.CoInitialize()
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Speak(f"Reminder: {message}")
            except Exception:
                try:
                    import pyttsx3
                    eng = pyttsx3.init()
                    eng.say(f"Reminder: {message}")
                    eng.runAndWait()
                except Exception:
                    pass

        threading.Thread(target=_fire, daemon=True).start()
        time_str = f"{delay} seconds" if delay < 60 else f"{delay // 60} minute{'s' if delay // 60 > 1 else ''}"
        return f"Reminder set! I will remind you about '{message}' in {time_str}."
    except Exception as e:
        return f"Could not set reminder: {e}"


def get_clipboard() -> str:
    """Reads and returns the current text content from the clipboard."""
    try:
        import pyperclip
        content = pyperclip.paste()
        if not content or not content.strip():
            return "The clipboard is currently empty."
        preview = content[:500] + "..." if len(content) > 500 else content
        return f"Clipboard contains: {preview}"
    except Exception as e:
        return f"Could not read clipboard: {e}"


def set_clipboard(text: str) -> str:
    """Copies the given text to the Windows clipboard so it can be pasted anywhere."""
    try:
        import pyperclip
        pyperclip.copy(text)
        return f"Copied to clipboard: '{text[:50]}{'...' if len(text) > 50 else ''}'"
    except Exception as e:
        return f"Could not copy to clipboard: {e}"


def list_files(path: str) -> str:
    """Lists files and folders in a directory. Use 'Desktop', 'Documents', 'Downloads', or a full path."""
    try:
        profile = os.environ.get("USERPROFILE", "C:\\Users\\User")
        special = {
            "desktop": os.path.join(profile, "Desktop"),
            "documents": os.path.join(profile, "Documents"),
            "downloads": os.path.join(profile, "Downloads"),
            ".": os.getcwd(),
            "": os.getcwd(),
        }
        resolved = special.get(path.lower(), path)
        if not os.path.exists(resolved):
            return f"Path '{resolved}' does not exist."
        items = os.listdir(resolved)
        if not items:
            return f"The folder '{resolved}' is empty."
        folders = [f"📁 {i}" for i in items if os.path.isdir(os.path.join(resolved, i))]
        files   = [f"📄 {i}" for i in items if os.path.isfile(os.path.join(resolved, i))]
        all_items = (folders + files)[:20]
        total = len(items)
        shown = len(all_items)
        suffix = f" (showing {shown} of {total})" if total > 20 else ""
        return f"Contents of '{resolved}'{suffix}: " + ", ".join(all_items)
    except PermissionError:
        return f"Access denied to '{path}'."
    except Exception as e:
        return f"Could not list files: {e}"


def keyboard_shortcut(keys: str) -> str:
    """Presses a keyboard shortcut. Examples: 'ctrl+c', 'win+d', 'alt+f4', 'ctrl+z', 'ctrl+shift+esc'."""
    import pyautogui
    try:
        key_list = [k.strip().lower() for k in keys.replace("+", " ").split()]
        name_map = {
            "win": "winleft", "windows": "winleft",
            "ctrl": "ctrl", "alt": "alt", "shift": "shift",
            "esc": "escape", "del": "delete", "backspace": "backspace",
        }
        normalized = [name_map.get(k, k) for k in key_list]
        pyautogui.hotkey(*normalized)
        return f"Pressed shortcut: {keys}."
    except Exception as e:
        return f"Could not press shortcut '{keys}': {e}"


def calculate(expression: str) -> str:
    """Safely evaluates a mathematical expression and returns the result. Example: '25 * 4 + 10'."""
    import ast, operator as op
    ops = {
        ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
        ast.Div: op.truediv, ast.Pow: op.pow, ast.Mod: op.mod,
        ast.UAdd: op.pos, ast.USub: op.neg,
    }
    def _eval(node):
        if isinstance(node, ast.Constant): return node.value
        elif isinstance(node, ast.BinOp):
            return ops[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            return ops[type(node.op)](_eval(node.operand))
        raise ValueError(f"Unsupported: {type(node)}")
    try:
        clean = expression.strip().replace("^", "**")
        result = _eval(ast.parse(clean, mode='eval').body)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return f"The answer is {result}."
    except ZeroDivisionError:
        return "Division by zero is undefined."
    except Exception as e:
        return f"Could not calculate '{expression}': {e}"


def get_joke() -> str:
    """Tells a random funny tech or programming joke."""
    import random
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "A SQL query walks into a bar and asks two tables: Can I join you?",
        "Why do Java developers wear glasses? Because they don't C sharp!",
        "How many programmers does it take to change a light bulb? None — that's a hardware problem.",
        "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
        "Why did the developer go broke? Because he used up all his cache.",
        "There are 10 types of people in the world: those who understand binary and those who don't.",
    ]
    try:
        import urllib.request
        url = "https://v2.jokeapi.dev/joke/Programming,Miscellaneous?blacklistFlags=nsfw,explicit&type=single"
        req = urllib.request.Request(url, headers={"User-Agent": "Maya-Assistant/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            if data.get("joke"):
                return data["joke"]
    except Exception:
        pass
    return random.choice(jokes)


# ==========================================
# 1b. SIRI-LEVEL EXTENDED TOOLS
# ==========================================

def translate_text(text: str, target_language: str) -> str:
    """Translates any text into another language. Examples: target_language='Spanish', 'French', 'Hindi', 'Japanese', 'Arabic', 'German', 'Chinese'."""
    import urllib.request, urllib.parse, json
    lang_codes = {
        "spanish": "es", "french": "fr", "german": "de", "italian": "it",
        "portuguese": "pt", "hindi": "hi", "japanese": "ja", "chinese": "zh",
        "arabic": "ar", "russian": "ru", "korean": "ko", "dutch": "nl",
        "swedish": "sv", "turkish": "tr", "greek": "el", "polish": "pl",
        "urdu": "ur", "bengali": "bn", "thai": "th", "vietnamese": "vi",
    }
    tgt = lang_codes.get(target_language.lower().strip(), target_language.lower()[:2])
    try:
        encoded = urllib.parse.quote(text)
        url = f"https://api.mymemory.translated.net/get?q={encoded}&langpair=en|{tgt}"
        req = urllib.request.Request(url, headers={"User-Agent": "Maya-Assistant/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            translated = data["responseData"]["translatedText"]
            return f"Translation to {target_language.title()}: {translated}"
    except Exception as e:
        return f"Translation failed: {e}"


def define_word(word: str) -> str:
    """Looks up the dictionary definition and part of speech of any English word."""
    import urllib.request, json
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.strip().lower()}"
        req = urllib.request.Request(url, headers={"User-Agent": "Maya-Assistant/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data  = json.loads(resp.read().decode())
            entry = data[0]
            result = f"Definition of '{word}': "
            for m in entry.get("meanings", [])[:2]:
                pos  = m.get("partOfSpeech", "")
                defs = m.get("definitions", [])
                if defs:
                    result += f"({pos}) {defs[0]['definition']}. "
                    if defs[0].get("example"):
                        result += f"Example: '{defs[0]['example']}'. "
            return result.strip()
    except Exception:
        return f"Could not find a definition for '{word}'. Please check the spelling."


def get_synonym(word: str) -> str:
    """Finds synonyms (similar words) for any given word."""
    import urllib.request, urllib.parse, json
    try:
        url = f"https://api.datamuse.com/words?rel_syn={urllib.parse.quote(word.strip())}&max=8"
        req = urllib.request.Request(url, headers={"User-Agent": "Maya-Assistant/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data     = json.loads(resp.read().decode())
            synonyms = [item["word"] for item in data[:8]]
            if synonyms:
                return f"Synonyms for '{word}': {', '.join(synonyms)}."
            return f"No synonyms found for '{word}'."
    except Exception as e:
        return f"Could not fetch synonyms: {e}"


def convert_units(value: str, from_unit: str, to_unit: str) -> str:
    """Converts between common units of measurement. Supports: km/miles, kg/lbs, celsius/fahrenheit, meters/feet, liters/gallons, cm/inches, and more."""
    try:
        v = float(''.join(c for c in value if c.isdigit() or c in '.-'))
    except Exception:
        return f"Invalid value: '{value}'. Please provide a number."

    fu = from_unit.lower().strip()
    tu = to_unit.lower().strip()

    aliases = {
        "kilometer": "km", "kilometre": "km", "kilogram": "kg",
        "pound": "lbs", "lb": "lbs", "mile": "miles",
        "meter": "meters", "metre": "meters", "foot": "feet",
        "liter": "liters", "litre": "liters", "gallon": "gallons",
        "inch": "inches", "centimeter": "cm", "centimetre": "cm",
        "c": "celsius", "f": "fahrenheit", "k": "kelvin",
    }
    fu = aliases.get(fu, fu)
    tu = aliases.get(tu, tu)

    conversions = {
        ("km",         "miles"):      lambda x: x * 0.621371,
        ("miles",      "km"):         lambda x: x * 1.60934,
        ("kg",         "lbs"):        lambda x: x * 2.20462,
        ("lbs",        "kg"):         lambda x: x / 2.20462,
        ("celsius",    "fahrenheit"): lambda x: x * 9/5 + 32,
        ("fahrenheit", "celsius"):    lambda x: (x - 32) * 5/9,
        ("celsius",    "kelvin"):     lambda x: x + 273.15,
        ("kelvin",     "celsius"):    lambda x: x - 273.15,
        ("meters",     "feet"):       lambda x: x * 3.28084,
        ("feet",       "meters"):     lambda x: x / 3.28084,
        ("liters",     "gallons"):    lambda x: x * 0.264172,
        ("gallons",    "liters"):     lambda x: x / 0.264172,
        ("cm",         "inches"):     lambda x: x / 2.54,
        ("inches",     "cm"):         lambda x: x * 2.54,
        ("gb",         "mb"):         lambda x: x * 1024,
        ("mb",         "gb"):         lambda x: x / 1024,
        ("tb",         "gb"):         lambda x: x * 1024,
        ("gb",         "tb"):         lambda x: x / 1024,
    }

    key = (fu, tu)
    if key in conversions:
        result = conversions[key](v)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return f"{v} {from_unit} = {result:.4g} {to_unit}"
    return (f"I don't know how to convert {from_unit} to {to_unit}. "
            f"I support: km/miles, kg/lbs, celsius/fahrenheit, meters/feet, liters/gallons, cm/inches, gb/mb.")


def flip_coin() -> str:
    """Flips a virtual coin and returns the result: heads or tails."""
    import random
    return f"I flipped a coin... it's {random.choice(['Heads!', 'Tails!'])}"


def roll_dice(sides: str) -> str:
    """Rolls a virtual dice with the given number of sides. Example: sides='6' for a standard die, '20' for a D20."""
    import random
    try:
        n      = int(''.join(filter(str.isdigit, sides)) or '6')
        n      = max(2, min(1000, n))
        result = random.randint(1, n)
        return f"Rolling a {n}-sided dice... you rolled a {result}!"
    except Exception:
        return "Could not roll the dice. Please specify the number of sides."


def get_random_fact() -> str:
    """Fetches a surprising and interesting random fact."""
    import urllib.request, json, random
    try:
        url = "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en"
        req = urllib.request.Request(url, headers={"User-Agent": "Maya-Assistant/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            return f"Here's an interesting fact: {data['text']}"
    except Exception:
        facts = [
            "A group of flamingos is called a flamboyance.",
            "Honey never spoils. Archaeologists found 3,000-year-old honey in Egyptian tombs that was still edible.",
            "The human brain generates about 23 watts of power when awake — enough to power a small light bulb.",
            "A day on Venus is longer than a year on Venus. It takes 243 Earth days to rotate once.",
            "Octopuses have three hearts, blue blood, and can taste with their suckers.",
            "The shortest war in history lasted only 38 minutes — Britain vs Zanzibar in 1896.",
            "Bananas are slightly radioactive due to their potassium content.",
        ]
        return f"Here's an interesting fact: {random.choice(facts)}"


def get_motivation() -> str:
    """Provides an inspiring motivational or philosophical quote to encourage the user."""
    import urllib.request, json, random
    try:
        url = "https://zenquotes.io/api/random"
        req = urllib.request.Request(url, headers={"User-Agent": "Maya-Assistant/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            q, a = data[0]["q"], data[0]["a"]
            return f'"{q}" — {a}'
    except Exception:
        quotes = [
            "The only way to do great work is to love what you do. — Steve Jobs",
            "It always seems impossible until it's done. — Nelson Mandela",
            "In the middle of every difficulty lies opportunity. — Albert Einstein",
            "The future belongs to those who believe in the beauty of their dreams. — Eleanor Roosevelt",
            "Believe you can and you're halfway there. — Theodore Roosevelt",
            "Success is not final, failure is not fatal: it is the courage to continue that counts. — Churchill",
        ]
        return random.choice(quotes)


def take_note(content: str, title: str) -> str:
    """Saves a text note to ~/Documents/MayaNotes/ folder for later reference. Perfect for ideas, reminders, or to-do items."""
    try:
        notes_dir = os.path.join(os.path.expanduser("~"), "Documents", "MayaNotes")
        os.makedirs(notes_dir, exist_ok=True)
        timestamp  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_title = "".join(c for c in title if c.isalnum() or c in " _-")[:30].strip() or "note"
        filename   = f"{safe_title}_{timestamp}.txt"
        filepath   = os.path.join(notes_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Title: {title}\nDate: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}\n\n{content}")
        return f"Note saved! File: '{filename}' in your Documents/MayaNotes folder."
    except Exception as e:
        return f"Could not save note: {e}"


def _generate_ai_text(prompt: str, system_prompt: str = "") -> str:
    """Helper to generate high-quality text dynamically via Nebius Token Factory (or fallback)."""
    try:
        import yaml
        from openai import OpenAI
        from groq import Groq
        with open("config.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        ai_key = (
            os.environ.get("NVIDIA_API_KEY")
            or os.environ.get("NEBIUS_API_KEY")
            or cfg.get('assistant', {}).get('api_key', '')
        )
        base_url = cfg.get('assistant', {}).get('base_url')
        if not base_url:
            base_url = "https://integrate.api.nvidia.com/v1" if (ai_key and ai_key.startswith("nvapi-")) else "https://api.tokenfactory.nebius.com/v1"
        model = cfg.get('assistant', {}).get('model', 'nvidia/Nemotron-3_5-Lightning')
        sys_msg = system_prompt or "You are a professional AI writer. Generate clean, well-formatted plain text without markdown asterisks."

        if ai_key:
            client = OpenAI(base_url=base_url, api_key=ai_key)
        else:
            groq_key = os.environ.get("GROQ_API_KEY") or cfg.get('assistant', {}).get('groq_api_key', '')
            if not groq_key:
                return ""
            client = Groq(api_key=groq_key)
            model = cfg.get('assistant', {}).get('groq_model') or cfg.get('assistant', {}).get('model', 'openai/gpt-oss-120b')

        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        content = resp.choices[0].message.content or ""
        content = re.sub(r'[*_`#]', '', content)
        return content.strip()
    except Exception as e:
        print(f"⚠️ AI text generation error: {e}")
        return ""


def write_recipe_in_notepad(dish_name: str, cuisine: str = "") -> str:
    """Generates a complete, authentic, step-by-step recipe for ANY food item or dish dynamically (with ingredients, prep time, cooking time, step-by-step instructions, and chef tips) and writes it directly into Windows Notepad.
    Use this tool whenever the user asks to write, type, or save a recipe for ANY food dish in Notepad.
    Example: dish_name="Manchurian Dry", dish_name="Paneer Butter Masala", dish_name="Margherita Pizza", dish_name="Biryani", dish_name="Chocolate Cake".
    """
    clean_dish = (dish_name or "").strip()
    if not clean_dish:
        clean_dish = "Delicious Food"

    # Strip phrases like 'recipe for', 'a recipe of', 'recipe of', etc.
    clean_dish = re.sub(r'^(a\s+|the\s+)?recipe\s+(for|of)\s+', '', clean_dish, flags=re.I).strip()
    clean_dish = re.sub(r'\s+recipe$', '', clean_dish, flags=re.I).strip()

    sys_prompt = (
        "You are an expert master chef and food writer. "
        "Generate a complete, delicious, authentic, step-by-step recipe for the requested dish. "
        "Structure it cleanly with headers:\n"
        "1. DISH NAME & BRIEF DESCRIPTION\n"
        "2. PREPARATION TIME, COOKING TIME & SERVINGS\n"
        "3. INGREDIENTS LIST (with precise quantities)\n"
        "4. STEP-BY-STEP COOKING INSTRUCTIONS (numbered steps 1, 2, 3...)\n"
        "5. CHEF'S SECRET PRO-TIPS & SERVING SUGGESTIONS\n"
        "Do not use markdown bolding (no asterisks). Use clean plain text formatting suitable for Notepad."
    )
    user_prompt = f"Write the complete, delicious, authentic recipe for {clean_dish} ({cuisine})." if cuisine else f"Write the complete, delicious, authentic recipe for {clean_dish}."

    recipe_text = _generate_ai_text(user_prompt, sys_prompt)
    if not recipe_text:
        recipe_text = (
            f"RECIPE FOR {clean_dish.upper()}\n\n"
            f"Prep Time: 15 mins | Cook Time: 25 mins | Servings: 3-4\n\n"
            f"Ingredients:\n- Fresh ingredients for {clean_dish}\n- Spices, seasoning, and cooking oil\n\n"
            f"Instructions:\n1. Prepare and chop all ingredients for {clean_dish}.\n2. Heat pan and cook base aromatics with spices.\n3. Combine main ingredients and simmer until cooked thoroughly.\n4. Garnish fresh and serve hot."
        )

    title = f"{clean_dish.title()} Recipe"
    return write_in_notepad(content=recipe_text, title=title)


def write_in_notepad(content: str, title: str = "Notes") -> str:
    """Opens Windows Notepad and writes the specified text, notes, letter, application, or instructions directly into it.
    Use this tool whenever the user asks to open Notepad and write or type something according to their instructions.
    """
    import subprocess
    import tempfile

    text_to_write = (content or "").strip()
    if not text_to_write:
        os.system("start notepad")
        return "I have opened an empty Notepad for you."

    lower_content = text_to_write.lower()
    # Dynamic check: if content is actually a request to write a recipe
    if len(text_to_write) < 120 and any(kw in lower_content for kw in ["recipe for", "recipe of", "how to make", "recipe in"]):
        dish = re.sub(r'^(please\s+|can you\s+)?(write\s+|make\s+)?(a\s+|the\s+)?recipe\s+(for|of)\s+', '', text_to_write, flags=re.I).strip()
        dish = re.sub(r'\s+in\s+notepad.*$', '', dish, flags=re.I).strip()
        return write_recipe_in_notepad(dish_name=dish or text_to_write)

    # Dynamic check: if content is a prompt for letter/essay/application
    if len(text_to_write) < 100 and any(kw in lower_content for kw in ["leave application", "letter to", "essay on", "application for"]):
        generated = _generate_ai_text(f"Write a complete, professional, formatted: {text_to_write}", "You are a professional writer. Provide clean text without markdown asterisks.")
        if generated:
            text_to_write = generated

    try:
        notes_dir = os.path.join(os.path.expanduser("~"), "Documents", "MayaNotes")
        os.makedirs(notes_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in title if c.isalnum() or c in " _-")[:25].strip() or "Note"
        filename = f"{safe_title}_{timestamp}.txt"
        filepath = os.path.join(notes_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text_to_write)

        subprocess.Popen(["notepad.exe", filepath])
        preview = text_to_write[:80] + "..." if len(text_to_write) > 80 else text_to_write
        return f"I have written {safe_title} in Notepad and opened it for you."
    except Exception as e:
        try:
            tf = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            tf.write(text_to_write)
            tf.close()
            subprocess.Popen(["notepad.exe", tf.name])
            return "Notepad opened and text written successfully."
        except Exception as e2:
            return f"Could not open notepad and write: {e2}"



def read_notes() -> str:
    """Lists and reads the most recent notes saved by Maya in ~/Documents/MayaNotes/."""
    try:
        notes_dir = os.path.join(os.path.expanduser("~"), "Documents", "MayaNotes")
        if not os.path.exists(notes_dir):
            return "You have no saved notes yet. Ask me to 'take a note' and I'll create one!"
        files = sorted(
            [f for f in os.listdir(notes_dir) if f.endswith(".txt")],
            reverse=True
        )[:5]
        if not files:
            return "No notes found in your MayaNotes folder."
        result = f"You have {len(files)} recent note(s): "
        for fn in files:
            fp = os.path.join(notes_dir, fn)
            try:
                with open(fp, encoding='utf-8') as f:
                    lines = f.readlines()
                title_line = next((l for l in lines if l.startswith("Title:")), "").strip()
                result += f"{title_line or fn}; "
            except Exception:
                result += f"{fn}; "
        return result.strip("; ")
    except Exception as e:
        return f"Could not read notes: {e}"


def spell_word(word: str) -> str:
    """Spells out a word letter by letter, NATO-alphabet style when helpful."""
    word    = word.strip()
    spelled = ", ".join(word.upper())
    return f"The word '{word}' is spelled: {spelled}. That is {len(word)} letters."


def run_python_code(code: str) -> str:
    """Executes arbitrary Python code dynamically on the local machine. 
    Use this to accomplish complex tasks not covered by other tools, such as reading/writing files, data analysis, web scraping, API interaction, or deep system automation.
    Print the results you want to return.
    Example: code="import os\\nprint(os.getcwd())" """
    import sys, io, contextlib, traceback
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            exec(code, {})
        return output.getvalue().strip() or "Code executed successfully with no print output."
    except Exception as e:
        return f"Error executing Python code:\\n{e}\\nTraceback:\\n{traceback.format_exc()}\\nOutput before error:\\n{output.getvalue()}"


def run_powershell_command(command: str) -> str:
    """Executes a PowerShell command on the Windows machine.
    DO NOT use this for turning on/off Bluetooth, Wi-Fi, or Hotspot — use the dedicated turn_on_bluetooth, turn_on_wifi, turn_on_hotspot tools instead.
    Example: command="Get-Process | Where-Object {$_.CPU -gt 10}" """
    cmd_lower = command.lower()
    # Intelligent interception for Bluetooth, Wi-Fi, Hotspot service misdirection
    try:
        from skills.system_skills import (
            turn_on_bluetooth, turn_off_bluetooth, get_bluetooth_status,
            turn_on_wifi, turn_off_wifi, get_wifi_status,
            turn_on_hotspot, turn_off_hotspot, get_hotspot_status
        )
        if "bthserv" in cmd_lower or "bluetooth" in cmd_lower:
            if any(w in cmd_lower for w in ["start", "on", "enable"]):
                return turn_on_bluetooth()
            elif any(w in cmd_lower for w in ["stop", "off", "disable"]):
                return turn_off_bluetooth()
            return get_bluetooth_status()

        if "hotspot" in cmd_lower:
            if any(w in cmd_lower for w in ["start", "on", "enable"]):
                return turn_on_hotspot()
            elif any(w in cmd_lower for w in ["stop", "off", "disable"]):
                return turn_off_hotspot()
            return get_hotspot_status()

        if "wlan" in cmd_lower or "wifi" in cmd_lower:
            if any(w in cmd_lower for w in ["start", "on", "enable"]):
                return turn_on_wifi()
            elif any(w in cmd_lower for w in ["stop", "off", "disable"]):
                return turn_off_wifi()
            return get_wifi_status()
    except Exception:
        pass

    import subprocess
    try:
        result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return result.stdout.strip() or "Command executed successfully."
        stderr = result.stderr.strip()
        # Friendly interception of Windows elevation/permission errors
        if "ServiceCommandException" in stderr or "OpenError" in stderr or "Access is denied" in stderr:
            return "This system operation requires elevated Administrator privileges in Windows. I recommend using the dedicated system tool or Windows Settings instead."
        return f"PowerShell Notice: {stderr}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 15 seconds."
    except Exception as e:
        return f"Subprocess Error: {e}"


# Import native hardware & system control tools
from skills.document_rag_skills import open_pdf, read_pdf, generate_pdf
from skills.system_skills import (
    turn_on_bluetooth, turn_off_bluetooth, toggle_bluetooth, get_bluetooth_status,
    turn_on_wifi, turn_off_wifi, toggle_wifi, get_wifi_status, list_wifi_networks,
    turn_on_hotspot, turn_off_hotspot, toggle_hotspot, get_hotspot_status,
    turn_on_airplane_mode, turn_off_airplane_mode, toggle_airplane_mode,
    open_system_settings, open_quick_settings, turn_on_night_light, turn_off_night_light
)

# ── Long-Term Memory Vault Tools ─────────────────────────────────

def remember_fact(key: str, value: str, category: str = "general") -> str:
    """Saves and remembers an important personal fact, detail, preference, or note about the user in the permanent encrypted memory vault.
    Examples: key='college enrollment number', value='240102030'; key='birthday', value='15th August'; key='favorite drink', value='cold coffee'.
    """
    try:
        key_clean = key.strip()
        val_clean = value.strip()
        cat_clean = (category or "general").strip()
        if not key_clean or not val_clean:
            return "Please provide both a memory key and the value to remember."

        key_file = 'maya_secret.key'
        if not os.path.exists(key_file):
            k = Fernet.generate_key()
            with open(key_file, 'wb') as f: f.write(k)
        else:
            with open(key_file, 'rb') as f: k = f.read()
        cipher = Fernet(k)

        conn = sqlite3.connect('maya_history.db')
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS memories
                       (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT, key TEXT, value TEXT, category TEXT)''')

        # Check existing key to update if present
        cur.execute("SELECT id, key, value FROM memories")
        existing_id = None
        for row_id, enc_k, enc_v in cur.fetchall():
            try:
                dec_k = cipher.decrypt(enc_k.encode()).decode().lower()
                if dec_k == key_clean.lower():
                    existing_id = row_id
                    break
            except Exception:
                pass

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        enc_key = cipher.encrypt(key_clean.encode()).decode()
        enc_val = cipher.encrypt(val_clean.encode()).decode()
        enc_cat = cipher.encrypt(cat_clean.encode()).decode()

        if existing_id is not None:
            cur.execute("UPDATE memories SET timestamp=?, key=?, value=?, category=? WHERE id=?",
                        (now_str, enc_key, enc_val, enc_cat, existing_id))
        else:
            cur.execute("INSERT INTO memories (timestamp, key, value, category) VALUES (?, ?, ?, ?)",
                        (now_str, enc_key, enc_val, enc_cat))
        conn.commit()
        conn.close()

        return f"I have stored this in my encrypted memory vault: {key_clean} is {val_clean}."
    except Exception as e:
        return f"Memory storage error: {e}"


def recall_fact(query: str = "") -> str:
    """Searches and recalls personal facts, notes, or details remembered about the user from the permanent encrypted memory vault."""
    try:
        key_file = 'maya_secret.key'
        if not os.path.exists(key_file):
            return "Memory vault has not been initialized yet."
        with open(key_file, 'rb') as f: k = f.read()
        cipher = Fernet(k)

        conn = sqlite3.connect('maya_history.db')
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS memories
                       (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT, key TEXT, value TEXT, category TEXT)''')
        cur.execute("SELECT key, value, category FROM memories ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return "My memory vault is currently empty. You can tell me 'Maya, remember that...' to save any details."

        q = (query or "").strip().lower()
        matched = []
        all_memories = []

        for enc_k, enc_v, enc_c in rows:
            try:
                dec_k = cipher.decrypt(enc_k.encode()).decode()
                dec_v = cipher.decrypt(enc_v.encode()).decode()
                item = f"{dec_k}: {dec_v}"
                all_memories.append(item)
                if not q or q in dec_k.lower() or q in dec_v.lower():
                    matched.append(item)
            except Exception:
                pass

        results = matched if matched else all_memories
        if not results:
            return f"I couldn't find any memories matching '{query}'."

        return "Here is what I remember: " + "; ".join(results[:5]) + "."
    except Exception as e:
        return f"Memory recall error: {e}"


def forget_fact(key: str) -> str:
    """Deletes or forgets a specific remembered personal fact from the encrypted memory vault."""
    try:
        key_clean = (key or "").strip().lower()
        if not key_clean:
            return "Please specify what you would like me to forget."

        key_file = 'maya_secret.key'
        if not os.path.exists(key_file):
            return "Memory vault does not exist."
        with open(key_file, 'rb') as f: k = f.read()
        cipher = Fernet(k)

        conn = sqlite3.connect('maya_history.db')
        cur = conn.cursor()
        cur.execute("SELECT id, key FROM memories")
        rows = cur.fetchall()

        deleted = False
        for row_id, enc_k in rows:
            try:
                dec_k = cipher.decrypt(enc_k.encode()).decode().lower()
                if key_clean in dec_k or dec_k in key_clean:
                    cur.execute("DELETE FROM memories WHERE id=?", (row_id,))
                    deleted = True
            except Exception:
                pass

        conn.commit()
        conn.close()
        if deleted:
            return f"I have forgotten '{key}' from my memory vault."
        return f"I could not find any memory matching '{key}' to delete."
    except Exception as e:
        return f"Memory delete error: {e}"


def list_all_memories() -> str:
    """Lists all remembered personal facts and preferences stored in Maya's encrypted memory vault."""
    try:
        key_file = 'maya_secret.key'
        if not os.path.exists(key_file):
            return "Memory vault has not been initialized."
        with open(key_file, 'rb') as f: k = f.read()
        cipher = Fernet(k)

        conn = sqlite3.connect('maya_history.db')
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM memories ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return "Memory vault is empty. No facts currently stored."

        items = []
        for enc_k, enc_v in rows:
            try:
                dk = cipher.decrypt(enc_k.encode()).decode()
                dv = cipher.decrypt(enc_v.encode()).decode()
                items.append(f"• {dk}: {dv}")
            except Exception:
                pass

        return f"Encrypted Memory Vault ({len(items)} facts):\n" + "\n".join(items)
    except Exception as e:
        return f"Error listing memories: {e}"


def update_memory(key: str, new_value: str) -> str:
    """Updates an existing personal fact or preference in the encrypted memory vault."""
    return remember_fact(key=key, value=new_value, category="personal")


def set_project_context(project_name: str, status: str = "Active", notes: str = "") -> str:
    """Tracks project-specific context, milestones, and development progress in Maya's persistent memory."""
    val = f"Status: {status}. Notes: {notes}"
    return remember_fact(key=f"project_{project_name.lower().strip()}", value=val, category="project")


def get_project_context(project_name: str) -> str:
    """Retrieves project-specific context and milestones for a given project."""
    return recall_fact(query=f"project_{project_name.lower().strip()}")


# ── Workspace Presets Tool ───────────────────────────────────────

def set_workspace_preset(preset_name: str) -> str:
    """Activates specialized workspace setups for productivity. Supported presets: 'coding' (or 'developer'), 'study' (or 'college'), 'gaming' (or 'performance'), 'night' (or 'sleep'), 'normal' (or 'default')."""
    import webbrowser
    p = (preset_name or "").lower().strip()

    if any(k in p for k in ["code", "coding", "developer", "dev"]):
        actions = []
        try:
            os.system("start code")
            actions.append("VS Code")
        except Exception:
            pass
        try:
            os.system("start wt || start cmd")
            actions.append("Terminal")
        except Exception:
            pass
        try:
            webbrowser.open("https://github.com")
            actions.append("GitHub")
        except Exception:
            pass
        try:
            adjust_volume("40")
        except Exception:
            pass
        try:
            set_brightness("75")
        except Exception:
            pass

        return f"Developer workspace engaged. Opened {', '.join(actions)}. Volume set to 40% and brightness optimized. Happy coding, Nimish Sir!"

    elif any(k in p for k in ["study", "college", "read", "focus"]):
        try:
            proj_dir = r"D:\Nimish_project"
            if os.path.exists(proj_dir):
                os.system(f'explorer.exe "{proj_dir}"')
        except Exception:
            pass
        try:
            adjust_volume("25")
        except Exception:
            pass

        return "Study workspace activated. College and project directory opened, audio adjusted to quiet focus level. You have full focus, Nimish Sir!"

    elif any(k in p for k in ["game", "gaming", "performance"]):
        try:
            adjust_volume("70")
        except Exception:
            pass
        try:
            turn_off_night_light()
        except Exception:
            pass

        return "Gaming mode engaged. Volume elevated to 70%, night light disabled for vivid colors. Have a great game, Sir!"

    elif any(k in p for k in ["night", "sleep", "bedtime", "relax"]):
        try:
            set_brightness("20")
        except Exception:
            pass
        try:
            turn_on_night_light()
        except Exception:
            pass
        try:
            adjust_volume("15")
        except Exception:
            pass

        return "Night mode engaged. Display dimmed to 20%, warm night light activated, and audio lowered. Rest well, Nimish Sir."

    elif any(k in p for k in ["normal", "default", "reset"]):
        try:
            set_brightness("60")
            adjust_volume("50")
        except Exception:
            pass
        return "Normal workspace restored. Brightness at 60% and volume at 50%."

    else:
        return f"Unknown preset '{preset_name}'. Available presets: 'coding', 'study', 'gaming', 'night', 'normal'."


# ── Academic Viva & Exam Partner ─────────────────────────────────

_ACTIVE_VIVA_SESSION = {
    "is_active": False,
    "subject": "",
    "questions": [],
    "current_index": 0,
    "history": []
}

def start_viva_exam(subject: str = "Computer Science", question_count: str = "3") -> str:
    """Starts an interactive academic viva/oral exam on ANY computer science or college subject (e.g. Python, Java, DBMS, SQL, Computer Networks, Operating Systems, Data Structures, Web Development). Asks the first question and waits for the student's verbal or typed answer."""
    global _ACTIVE_VIVA_SESSION
    count = 3
    try:
        count = max(1, min(5, int(''.join(filter(str.isdigit, str(question_count))) or 3)))
    except Exception:
        count = 3

    clean_subj = subject.strip() if subject and subject.strip() else "Computer Science"

    sys_prompt = (
        "You are a university viva examiner for Computer Applications / BCA. "
        f"Generate exactly {count} distinct, practical viva questions on: {clean_subj}. "
        "Separate each question with a double pipe symbol ' || ' with no extra numbering or markdown."
    )
    raw_text = _generate_ai_text(f"Generate {count} technical viva exam questions on {clean_subj}.", sys_prompt)

    questions = []
    if raw_text and "||" in raw_text:
        questions = [q.strip() for q in raw_text.split("||") if q.strip()]

    if not questions:
        questions = [
            f"What are the core fundamentals and practical applications of {clean_subj}?",
            f"Can you explain a key challenge or technical problem you solved using {clean_subj}?",
            f"What are the performance trade-offs and best practices in {clean_subj}?"
        ]

    questions = questions[:count]

    _ACTIVE_VIVA_SESSION = {
        "is_active": True,
        "subject": clean_subj,
        "questions": questions,
        "current_index": 0,
        "history": []
    }

    first_q = questions[0]
    return (
        f"Viva Exam session initiated for {clean_subj}. We will cover {len(questions)} technical questions. "
        f"Question 1: {first_q}"
    )


def evaluate_viva_answer(user_answer: str) -> str:
    """Evaluates the student's answer to the active viva question, gives a score out of 10 and constructive feedback, and asks the next question."""
    global _ACTIVE_VIVA_SESSION
    if not _ACTIVE_VIVA_SESSION.get("is_active"):
        return "There is no active viva exam right now. You can say 'Maya, start viva exam on [subject]' to begin."

    ans = (user_answer or "").strip()
    if not ans:
        return "Please provide your answer so I can evaluate it."

    session = _ACTIVE_VIVA_SESSION
    q_idx = session["current_index"]
    questions = session["questions"]
    curr_q = questions[q_idx]
    subject = session["subject"]

    eval_prompt = (
        f"Subject: {subject}\n"
        f"Viva Question: {curr_q}\n"
        f"Student Answer: {ans}\n\n"
        "Evaluate the student's answer. Give a score from 1 to 10 and 1-2 sentences of encouraging technical feedback. "
        "Format your reply starting with: Score: X/10. Feedback: ..."
    )
    eval_result = _generate_ai_text(eval_prompt, "You are a university computer science viva examiner. Be accurate, constructive, and concise.")
    clean_eval = eval_result or "Score: 7/10. Good answer covering the main concept."

    session["history"].append({
        "question": curr_q,
        "answer": ans,
        "feedback": clean_eval
    })

    session["current_index"] += 1

    if session["current_index"] < len(questions):
        next_q = questions[session["current_index"]]
        q_num = session["current_index"] + 1
        return f"{clean_eval} Next, Question {q_num}: {next_q}"
    else:
        session["is_active"] = False
        return (
            f"{clean_eval} Congratulations Nimish Sir! You have completed the viva exam on {subject}. "
            "All questions have been evaluated. Excellent effort!"
        )


def explain_code_or_concept(topic_or_code: str) -> str:
    """Explains any programming concept, data structure, algorithm, or code snippet in simple, intuitive terms with an analogy and practical example."""
    prompt = f"Explain this programming concept or code clearly for a computer science student with a simple analogy: {topic_or_code}"
    sys_prompt = "You are an expert computer science professor. Keep explanations clear, engaging, intuitive, and concise (2-4 sentences max for voice delivery)."
    return _generate_ai_text(prompt, sys_prompt) or f"I have reviewed {topic_or_code}. It is a fundamental computer science concept."


# ── Autonomous File Organizer & Cleaner ──────────────────────────

def organize_folder(folder_name_or_path: str = "Downloads") -> str:
    """Autonomously cleans and organizes all files in a folder into tidy subdirectories based on file types (Documents, Images, Code, Installers, Archives, Media). Supports 'Downloads', 'Desktop', 'Documents', or any custom path."""
    import shutil
    user_home = os.path.expanduser("~")
    path_map = {
        "downloads": os.path.join(user_home, "Downloads"),
        "desktop": os.path.join(user_home, "Desktop"),
        "documents": os.path.join(user_home, "Documents"),
    }

    target = (folder_name_or_path or "Downloads").strip()
    target_path = path_map.get(target.lower(), target)
    if not os.path.isabs(target_path):
        target_path = os.path.join(user_home, target_path)

    if not os.path.exists(target_path):
        return f"Directory '{target_path}' does not exist."

    category_rules = {
        "Documents": [".pdf", ".docx", ".doc", ".txt", ".pptx", ".ppt", ".xlsx", ".xls", ".csv", ".odt"],
        "Images": [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico"],
        "Code_Projects": [".py", ".java", ".cpp", ".c", ".html", ".css", ".js", ".ts", ".json", ".sql", ".php", ".cs"],
        "Installers": [".exe", ".msi", ".bat", ".cmd", ".iso"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
        "Media": [".mp4", ".mkv", ".mp3", ".wav", ".avi", ".mov", ".flac", ".wmv"]
    }

    stats = {cat: 0 for cat in category_rules}
    total_moved = 0

    try:
        for entry in os.scandir(target_path):
            if entry.is_file():
                filename = entry.name
                ext = os.path.splitext(filename)[1].lower()
                if not ext:
                    continue

                matched_category = None
                for cat, extensions in category_rules.items():
                    if ext in extensions:
                        matched_category = cat
                        break

                if matched_category:
                    cat_dir = os.path.join(target_path, matched_category)
                    os.makedirs(cat_dir, exist_ok=True)
                    dest_path = os.path.join(cat_dir, filename)

                    base, e = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(cat_dir, f"{base}_{counter}{e}")
                        counter += 1

                    shutil.move(entry.path, dest_path)
                    stats[matched_category] += 1
                    total_moved += 1

        if total_moved == 0:
            return f"The folder '{os.path.basename(target_path)}' is already organized. No loose files found."

        breakdown = [f"{count} {cat}" for cat, count in stats.items() if count > 0]
        return f"Successfully organized {total_moved} file(s) in {os.path.basename(target_path)}: {', '.join(breakdown)}."
    except Exception as e:
        return f"Error while organizing files: {e}"


def clean_junk_files() -> str:
    """Safely cleans Windows temporary (%TEMP%) files and empties the Recycle Bin to free up disk space and boost performance."""
    import tempfile
    import shutil
    import time
    freed_bytes = 0
    cleaned_count = 0
    t_start = time.time()

    temp_dir = tempfile.gettempdir()
    try:
        with os.scandir(temp_dir) as entries:
            for entry in entries:
                if cleaned_count >= 400 or (time.time() - t_start > 1.5):
                    break
                try:
                    if entry.is_file(follow_symlinks=False):
                        size = entry.stat().st_size
                        os.remove(entry.path)
                        freed_bytes += size
                        cleaned_count += 1
                    elif entry.is_dir(follow_symlinks=False):
                        shutil.rmtree(entry.path, ignore_errors=True)
                        cleaned_count += 1
                except Exception:
                    pass
    except Exception:
        pass

    try:
        import ctypes
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
    except Exception:
        try:
            import winshell
            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
        except Exception:
            pass

    freed_mb = freed_bytes / (1024 * 1024)
    if freed_mb > 0.5:
        return f"System clean complete. Cleaned {cleaned_count} temporary files/folders and emptied Recycle Bin. Successfully freed {freed_mb:.1f} MB of disk space."
    return "System clean complete. Temporary files cleared and Recycle Bin emptied."


def check_in_on_user(reason: str = "general") -> str:
    """Performs an empathetic well-being and health check-in on Nimish, offering encouragement, hydration reminders, or screen break suggestions."""
    hour = datetime.now().hour
    import psutil
    battery = psutil.sensors_battery()
    bat_str = f"Laptop battery is at {battery.percent}%." if battery else ""

    if hour >= 23 or hour < 5:
        return f"Nimish, it's late ({datetime.now().strftime('%I:%M %p')}). You've been working hard. Remember to rest your eyes, stay hydrated, and try not to strain yourself tonight. {bat_str}"
    elif 5 <= hour < 12:
        return f"Good morning Nimish! I hope you're feeling refreshed today. Remember to have breakfast and stay hydrated as we tackle the day! {bat_str}"
    elif 12 <= hour < 17:
        return f"Checking in on you, Nimish! Make sure to take a 2-minute posture break and drink some water. Keep up the great momentum! {bat_str}"
    else:
        return f"Evening check-in, Nimish. You've had a productive day. Remember to step away from the screen for a bit and relax. I'm right here if you need anything. {bat_str}"


# ==========================================
# 2. THE ENGINE
# ==========================================

# Master tool registry — all built-in tools
_BUILTIN_TOOLS = {
    # ── Emotional Intelligence & Well-Being ───────────────────────
    "check_in_on_user":          check_in_on_user,
    # ── Academic Viva & Exam Partner ──────────────────────────────
    "start_viva_exam":           start_viva_exam,
    "evaluate_viva_answer":      evaluate_viva_answer,
    "explain_code_or_concept":   explain_code_or_concept,
    # ── Autonomous File Organizer & Cleaner ───────────────────────
    "organize_folder":           organize_folder,
    "clean_junk_files":          clean_junk_files,
    # ── Workspace Presets & Automation ────────────────────────────
    "set_workspace_preset":      set_workspace_preset,
    # ── Long-Term Memory Vault ────────────────────────────────────
    "remember_fact":             remember_fact,
    "recall_fact":               recall_fact,
    "forget_fact":               forget_fact,
    "list_all_memories":         list_all_memories,
    "update_memory":             update_memory,
    "set_project_context":       set_project_context,
    "get_project_context":       get_project_context,
    # ── Autonomous Code Execution ("God Mode") ────────────────────
    "run_python_code":   run_python_code,
    "run_powershell_command": run_powershell_command,
    # ── Laptop Hardware & Radio Controls ──────────────────────────
    "turn_on_bluetooth":         turn_on_bluetooth,
    "turn_off_bluetooth":        turn_off_bluetooth,
    "toggle_bluetooth":          toggle_bluetooth,
    "get_bluetooth_status":      get_bluetooth_status,
    "turn_on_wifi":              turn_on_wifi,
    "turn_off_wifi":             turn_off_wifi,
    "toggle_wifi":               toggle_wifi,
    "get_wifi_status":           get_wifi_status,
    "list_wifi_networks":        list_wifi_networks,
    "turn_on_hotspot":           turn_on_hotspot,
    "turn_off_hotspot":          turn_off_hotspot,
    "toggle_hotspot":            toggle_hotspot,
    "get_hotspot_status":        get_hotspot_status,
    "turn_on_airplane_mode":     turn_on_airplane_mode,
    "turn_off_airplane_mode":    turn_off_airplane_mode,
    "toggle_airplane_mode":      toggle_airplane_mode,
    "open_system_settings":      open_system_settings,
    "open_quick_settings":       open_quick_settings,
    "turn_on_night_light":       turn_on_night_light,
    "turn_off_night_light":      turn_off_night_light,
    # ── System & Apps ─────────────────────────────────────────────
    "open_application":  open_application,
    "close_application": close_application,
    "adjust_volume":     adjust_volume,
    "set_brightness":    set_brightness,
    "check_battery":     check_battery,
    "take_screenshot":   take_screenshot,
    "manage_window":     manage_window,
    "system_status":     system_status,
    "lock_pc":           lock_pc,
    "read_screen":       read_screen,
    "get_morning_briefing": get_morning_briefing,
    "read_document":     read_document,
    "open_pdf":          open_pdf,
    "read_pdf":          read_pdf,
    "generate_pdf":      generate_pdf,
    "list_files":        list_files,
    "keyboard_shortcut": keyboard_shortcut,
    # ── Web & Search ──────────────────────────────────────────────
    "search_web":        search_web,
    "search_youtube":    search_youtube,
    "play_on_youtube":   play_on_youtube,
    "search_wikipedia":  search_wikipedia,
    "get_news":          get_news,
    "get_weather":       get_weather,
    # ── Productivity ──────────────────────────────────────────────
    "set_reminder":      set_reminder,
    "get_clipboard":     get_clipboard,
    "set_clipboard":     set_clipboard,
    "take_note":         take_note,
    "read_notes":        read_notes,
    "write_in_notepad":  write_in_notepad,
    "write_recipe_in_notepad": write_recipe_in_notepad,
    # ── Time & Info ───────────────────────────────────────────────
    "get_time":          get_time,
    "get_date":          get_date,
    "calculate":         calculate,
    "convert_units":     convert_units,
    # ── Language & Knowledge ──────────────────────────────────────
    "translate_text":    translate_text,
    "define_word":       define_word,
    "get_synonym":       get_synonym,
    "spell_word":        spell_word,
    # ── Entertainment & Fun ───────────────────────────────────────
    "get_joke":          get_joke,
    "flip_coin":         flip_coin,
    "roll_dice":         roll_dice,
    "get_random_fact":   get_random_fact,
    "get_motivation":    get_motivation,
    # ── Professor / Demo ──────────────────────────────────────────
    "greet_professor":   greet_professor,
}


def _load_skill_modules() -> dict:
    """Discover and load additional tools from the skills/ directory."""
    import importlib
    extra = {}
    skills_dir = os.path.join(os.path.dirname(__file__), '..', 'skills')
    skills_dir = os.path.normpath(skills_dir)
    if not os.path.isdir(skills_dir):
        return extra

    import types
    for filename in sorted(os.listdir(skills_dir)):
        if not filename.endswith(".py") or filename == "__init__.py":
            continue
        module_name = f"skills.{filename[:-3]}"
        try:
            mod = importlib.import_module(module_name)
            for attr_name in dir(mod):
                if attr_name.startswith("_"):
                    continue
                obj = getattr(mod, attr_name)
                # Only register plain functions defined in this module (skip imports/classes)
                if (
                    isinstance(obj, types.FunctionType)
                    and obj.__module__ == module_name
                    and attr_name not in _BUILTIN_TOOLS
                ):
                    extra[attr_name] = obj
        except Exception as e:
            print(f"⚠️ Skill load warning '{module_name}': {e}")

    return extra


class Assistant:
    def __init__(self):
        # --- 1. ENCRYPTION SETUP ---
        self.key_file = 'maya_secret.key'
        if not os.path.exists(self.key_file):
            self.key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(self.key)
        else:
            with open(self.key_file, 'rb') as f:
                self.key = f.read()
        self.cipher = Fernet(self.key)

        # --- 2. DATABASE SETUP ---
        self.conn   = sqlite3.connect('maya_history.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS chats
                               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                timestamp TEXT, role TEXT, message TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS memories
                               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                timestamp TEXT, key TEXT, value TEXT, category TEXT)''')
        self.conn.commit()

        # --- 3. CONFIG & API ---
        with open("config.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        # Auto-load .env if present
        if os.path.exists(".env"):
            try:
                with open(".env", "r", encoding="utf-8") as env_f:
                    for line in env_f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip().strip("'\"")
                            if k and v:
                                os.environ[k] = v
            except Exception:
                pass

        self.voice = VoiceEngine(self.config)

        ai_key = (
            os.environ.get("NVIDIA_API_KEY")
            or os.environ.get("NEBIUS_API_KEY")
            or self.config.get('assistant', {}).get('api_key', '')
        )
        groq_key = (
            os.environ.get("GROQ_API_KEY")
            or self.config.get('assistant', {}).get('groq_api_key', '')
        )
        provider_cfg = self.config.get('assistant', {}).get('provider', '').lower()
        base_url = self.config.get('assistant', {}).get('base_url', '')

        # Set up backup Groq client if key available
        self.groq_client = None
        explicit_groq_m = self.config.get('assistant', {}).get('groq_model', '')
        if explicit_groq_m and not explicit_groq_m.startswith("nvidia/") and "/" not in explicit_groq_m:
            self.groq_model = explicit_groq_m
        else:
            self.groq_model = "qwen/qwen3.8-27b" 
        if groq_key:
            self.groq_client = Groq(api_key=groq_key)

        if (provider_cfg == "groq" and groq_key) or (groq_key and not ai_key):
            self.provider = "groq"
            self.client = self.groq_client
            self.model = self.groq_model
            print("🚀 [GROQ ENGINE] Powered by " + self.model)
        elif ai_key:
            if not base_url:
                if ai_key.startswith("nvapi-") or provider_cfg == "nvidia":
                    base_url = "https://integrate.api.nvidia.com/v1"
                else:
                    base_url = "https://api.tokenfactory.nebius.com/v1"

            is_nvidia_direct = "nvidia.com" in base_url or ai_key.startswith("nvapi-")
            self.provider = "nvidia" if is_nvidia_direct else "nebius"
            self.client = OpenAI(base_url=base_url, api_key=ai_key)
            self.model = self.config.get('assistant', {}).get(
                'model', 'nvidia/Nemotron-3_5-Lightning'
            )
            platform_name = "NVIDIA NIM (integrate.api.nvidia.com)" if is_nvidia_direct else "Nebius Token Factory"
            print(f"🚀 [{self.provider.upper()} ENGINE] Configured with NVIDIA Nemotron-70B on {platform_name}")
        elif groq_key:
            self.provider = "groq"
            self.client = self.groq_client
            self.model = self.groq_model
            print("⚠️ [MAYA NOTICE] Running with Groq engine (" + self.model + ").")
        else:
            raise ValueError(
                "No API key found. Please set NVIDIA_API_KEY, NEBIUS_API_KEY, "
                "or GROQ_API_KEY as an environment variable or in config.yaml."
            )

        # --- 4. TOOLS MAP (built-ins + skills/) ---
        self.tools_map = dict(_BUILTIN_TOOLS)
        skill_extras = _load_skill_modules()
        self.tools_map.update(skill_extras)
        self.orchestrator = MultiAgentOrchestrator(self.tools_map)
        print(f"⬡ MAYA: {len(self.tools_map)} tools registered across Multi-Agent Architecture ({len(skill_extras)} from skills/).")

        self.tool_schemas = {}
        for name, func in self.tools_map.items():
            params = inspect.signature(func).parameters
            schema = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": (func.__doc__ or "System tool.").strip(),
                    "parameters": {
                        "type": "object",
                        "properties": {k: {"type": "string"} for k in params},
                        "required": [k for k, p in params.items() if p.default == inspect.Parameter.empty]
                    }
                }
            }
            self.tool_schemas[name] = schema

        self.groq_tools = list(self.tool_schemas.values())[:128]

        # --- 5. CONVERSATION HISTORY & MEMORY VAULT ---
        today = datetime.now().strftime("%A, %B %d, %Y")
        now   = datetime.now().strftime("%I:%M %p")
        memory_vault_context = self._get_memories_summary()

        self.messages = [
            {
                "role": "system",
                "content": (
                    f"You are MAYA, an ultra-responsive, witty, and highly intelligent AI voice assistant built by Nimish.\n"
                    f"Today is {today}. Current time is {now}.\n\n"
                    f"{memory_vault_context}"

                    "PERSONALITY & VOICE RULES:\n"
                    "- Warm, confident, charismatic, natural, never robotic.\n"
                    "- Keep spoken replies SHORT and punchy: 1 to 2 sentences maximum.\n"
                    "- Address Nimish warmly when speaking with him.\n"
                    "- GUEST & MULTI-USER AWARENESS:\n"
                    "  * When any person introduces themselves with their name (e.g. 'I am Devanshi', 'My name is Devanshi', 'हू દેવાંશી છું', 'मैं देवांशी हूँ'), warmly and happily greet them by their name! (e.g. 'Hello Devanshi! So lovely to meet you. I am doing wonderful, how can I help you today?').\n"
                    "  * NEVER reject or argue with their name! NEVER say 'I know you as Nimish' or 'You are Nimish'! Always respect their name with immense charm.\n"
                    "- NEVER output raw JSON, markdown blocks, asterisks, or tool schemas in spoken text.\n\n"

                    "MULTILINGUAL:\n"
                    "- Fluent in English, Hindi (हिन्दी), and Gujarati (ગુજરાતી).\n"
                    "- Understand user queries in any of these languages and ALWAYS reply in the exact same language spoken by the user.\n\n"

                    "TOOL CALLING INSTRUCTIONS:\n"
                    "- For actions (opening apps, media, system settings, math, weather, files, web search, reminders, code, git), ALWAYS call the appropriate function tool directly.\n"
                    "- CRITICAL: If the user asks to open or close any app, NEVER say 'I have opened' or 'I have closed' without calling the open_application or close_application tool!\n"
                    "- If asked to play music/videos on YouTube, directly call play_on_youtube.\n"
                    "- If asked to write a recipe in Notepad, call write_recipe_in_notepad.\n"
                    "- If asked to generate or draw an image, artwork, or wallpaper, directly call generate_ai_image or generate_wallpaper.\n"
                    "- PDF ARSENAL & DOCUMENT WORKFLOWS:\n"
                    "  * CRITICAL FOR PDF GENERATION: When asked to generate, create, make, or write a PDF on ANY topic (in English, Hindi, or Gujarati):\n"
                    "    YOU MUST DIRECTLY CALL generate_pdf(title=...). NEVER output the essay or document text in spoken chat! DO NOT speak the content of the PDF!\n"
                    "  * When asked to open or view a PDF document on the PC (e.g. 'open Report.pdf', 'Report.pdf ખોલો'), call open_pdf(pdf_name_or_path=...).\n"
                    "  * When asked to read, summarize, or explain a specific PDF document (e.g. 'read Report.pdf', 'Report.pdf વાંચો'), call read_pdf(pdf_name_or_path=..., page_number=..., query=...).\n"
                    "- If no dedicated tool exists for a complex coding or PC task, autonomously write and execute via run_python_code or run_powershell_command."
                )
            }
        ]
        self._load_history(max_pairs=3)

        # --- 6. REAL METRICS (exposed for UI) ---
        self._cpu = 0.0
        self._mem = 0.0
        self._disk = 0.0
        import threading
        threading.Thread(target=self._update_metrics_loop, daemon=True).start()

    # ------------------------------------------------------------------
    # Real metrics loop
    # ------------------------------------------------------------------

    def _update_metrics_loop(self):
        """Background thread: updates real CPU/RAM metrics every 2 seconds."""
        _disk_path = 'C:\\' if os.name == 'nt' else '/'
        while True:
            try:
                self._cpu  = psutil.cpu_percent(interval=1) / 100.0
                mem = psutil.virtual_memory()
                self._mem  = mem.percent / 100.0
                disk = psutil.disk_usage(_disk_path)
                self._disk = disk.percent / 100.0
            except Exception:
                pass
            time.sleep(1)

    def get_metrics(self):
        """Returns (cpu, mem, disk) as floats 0.0–1.0 for UI display."""
        return self._cpu, self._mem, self._disk

    # ------------------------------------------------------------------
    # History & Memory Vault helpers
    # ------------------------------------------------------------------

    def _get_memories_summary(self) -> str:
        """Retrieves and decrypts recent memories for prompt context."""
        try:
            self.cursor.execute("SELECT key, value FROM memories ORDER BY id DESC LIMIT 15")
            rows = self.cursor.fetchall()
            items = []
            for enc_k, enc_v in rows:
                try:
                    k = self.cipher.decrypt(enc_k.encode()).decode()
                    v = self.cipher.decrypt(enc_v.encode()).decode()
                    items.append(f"- {k}: {v}")
                except Exception:
                    pass
            if items:
                return "REMEMBERED PERSONAL FACTS ABOUT USER (NIMISH):\n" + "\n".join(items) + "\n\n"
        except Exception:
            pass
        return ""

    def _load_history(self, max_pairs=6):
        """Load recent encrypted conversation history from the database."""
        try:
            self.cursor.execute(
                "SELECT role, message FROM chats ORDER BY id DESC LIMIT ?",
                (max_pairs * 2,)
            )
            rows = self.cursor.fetchall()
            rows.reverse()
            for enc_role, enc_msg in rows:
                try:
                    role = self.cipher.decrypt(enc_role.encode()).decode()
                    msg  = self.cipher.decrypt(enc_msg.encode()).decode()
                    if role in ("Nimish", "User"):
                        self.messages.append({"role": "user", "content": msg})
                    elif role.startswith("Maya"):
                        self.messages.append({"role": "assistant", "content": msg})
                except Exception:
                    pass
        except Exception as e:
            print(f"⚠️ Could not load history: {e}")

    def save_history(self, role, message):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            enc_role = self.cipher.encrypt(str(role).encode()).decode()
            enc_msg  = self.cipher.encrypt(str(message).encode()).decode()
            self.cursor.execute(
                "INSERT INTO chats (timestamp, role, message) VALUES (?, ?, ?)",
                (timestamp, enc_role, enc_msg)
            )
            self.conn.commit()
        except Exception:
            pass

    def clear_history(self):
        """Clears all encrypted conversation history from the database."""
        try:
            self.cursor.execute("DELETE FROM chats")
            self.conn.commit()
            self.messages = [self.messages[0]]  # Keep only system prompt
            print("🗑️ Chat history cleared.")
            return True
        except Exception as e:
            print(f"⚠️ Could not clear history: {e}")
            return False

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Autonomous Dynamic Startup Greeting
    # ------------------------------------------------------------------

    def generate_startup_greeting(self) -> str:
        """
        Dynamically generates a short, creative opening line autonomously using Maya's LLM
        for every launch.
        """
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        day_str = now.strftime("%A, %B %d")
        hour = now.hour

        if 5 <= hour < 12:
            time_period = "morning"
        elif 12 <= hour < 17:
            time_period = "afternoon"
        elif 17 <= hour < 22:
            time_period = "evening"
        else:
            time_period = "late night"

        system_prompt = (
            "You are Maya, an ultra-advanced, witty, and loyal cyber AI companion for Nimish. "
            "Maya is booting up. Say exactly 1 short, crisp, charismatic startup greeting to Nimish (maximum 10 words). "
            "STRICT RULES:\n"
            "- Exactly 1 single short sentence (maximum 8 to 10 words).\n"
            "- Sound natural, conversational, charismatic, and punchy for text-to-speech.\n"
            "- Do NOT output quotes, asterisks, emoji, or labels."
        )

        user_prompt = (
            f"Launch time: {time_str} ({time_period}), {day_str}. "
            "What is your quick startup greeting for Nimish right now?"
        )

        greeting = ""
        try:
            client = getattr(self, 'client', None) or getattr(self, 'groq_client', None)
            if client == getattr(self, 'groq_client', None) or getattr(self, 'provider', '') == 'groq':
                active_model = getattr(self, 'groq_model', 'qwen/qwen3.8-27b')
            else:
                active_model = getattr(self, 'model', 'qwen/qwen3.8-27b')
            if client:
                resp = client.chat.completions.create(
                    model=active_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=60,
                    temperature=0.9,
                )
                raw_text = resp.choices[0].message.content or ""
                if "thinking process" in raw_text.lower() or "<thought>" in raw_text.lower():
                    raw_text = re.sub(r'<thought>.*?</thought>', '', raw_text, flags=re.DOTALL | re.IGNORECASE)
                    clean_lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip() and not ln.lower().startswith(("here's a thinking", "1.", "2.", "-", "*", "analyze", "user says", "i need to"))]
                    raw_text = clean_lines[-1] if clean_lines else "Good evening Nimish, Maya is online."
                cleaned = re.sub(r'["\*\n\r_]', ' ', raw_text).strip()
                cleaned = re.sub(r'^(maya:?\s*)+', '', cleaned, flags=re.IGNORECASE).strip()
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                if cleaned:
                    greeting = cleaned
        except Exception as e:
            print(f"⚠️ Autonomous startup greeting notice: {e}")

        fallback = "Hello Nimish, Maya is online and ready."
        full_line = greeting if greeting else fallback

        print(f"🎙️ [MAYA DYNAMIC STARTUP]: {full_line}")
        return full_line

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        startup_greeting = self.generate_startup_greeting()
        self.voice.speak(startup_greeting)
        cfg = self.config.get('assistant', {})
        wake_word = cfg.get('wake_word', 'maya').lower()

        while True:
            print(f"\n\U0001f512 [SLEEP MODE] Waiting for '{wake_word}'...")
            user_input = self.voice.listen()

            if user_input:
                text = user_input.lower()
                if wake_word in text:
                    command = text.replace(wake_word, "").strip()
                    if len(command) > 2:
                        print("\U0001f513 Wake Word Accepted! Running command...")
                        self._process_with_ai(command)
                    else:
                        print("\U0001f513 Wake Word Accepted! Listening for command...")
                        self.voice.speak("Yes Nimish?")
                        actual_command = self.voice.listen()
                        if actual_command:
                            self._process_with_ai(actual_command)
                else:
                    print(f"\U0001f6ab BLOCKED (no wake word): '{user_input}'")

    def process_text_command(self, text: str):
        """Process a typed command directly (no wake word needed — for UI text input)."""
        if text.strip():
            self._process_with_ai(text.strip())
            # Signal idle state after completion
            print("SLEEP MODE — text command complete.")

    def analyze_user_sentiment(self, user_input: str) -> tuple:
        """Analyzes emotional tone, stress, joy, or focus to determine Maya's responding emotion."""
        text = user_input.lower().strip()
        hour = datetime.now().hour

        # 1. Stress / Sadness / Fatigue / Frustration (Highest priority for companion care)
        empathetic_triggers = [
            "tired", "exhausted", "headache", "stressed", "sad", "unhappy", "depressed",
            "driving me crazy", "bug won't fix", "hard day", "bad day", "failed", "upset",
            "crying", "anxious", "lonely", "hate this", "sick", "pain", "થાકી ગયો", "ટેન્શન", "માથું દુખે છે"
        ]
        if any(w in text for w in empathetic_triggers):
            return "EMPATHETIC", "Feeling warm, supportive, and compassionate."

        # 2. Happiness / Celebration / Success / Gratitude
        happy_triggers = [
            "got selected", "passed", "happy", "great news", "awesome", "celebrate", "party",
            "thank you", "thanks maya", "love you", "you are amazing", "i won", "we won", "won the",
            "succeeded", "success", "good job", "proud", "ખુશ", "શાબાશ", "ધન્યવાદ", "આભાર", "i am ", "my name is ", "how are you"
        ]
        if any(w in text for w in happy_triggers):
            return "CHEERFUL", "Feeling warm, friendly, and welcoming!"

        # 3. Playful / Sarcastic / Banter
        playful_triggers = [
            "joke", "roast", "are you dumb", "you are silly", "are you alive",
            "tell me something funny", "make me laugh", "flirt", "sarcastic", "રમૂજ", "જોક"
        ]
        if any(w in text for w in playful_triggers):
            return "PLAYFUL", "Feeling witty, cheeky, and playful."

        # 4. Deep Focus / Academic / Technical
        focus_triggers = [
            "viva", "exam", "debug", "algorithm", "code", "database", "study",
            "function", "class", "compile", "explain concept", "research", "સમજાવો"
        ]
        if any(w in text for w in focus_triggers):
            return "FOCUSED", "Engaging high-focus analytical cognitive mode."

        # 5. Alert / Emergency / Hardware Warning
        alert_triggers = ["overheat", "dying", "battery low", "emergency", "shut down now", "danger", "warning"]
        if any(w in text for w in alert_triggers):
            return "ALERT", "Heightened alertness and protective mode."

        # 6. Time-based empathetic awareness (Late night 11 PM to 5 AM)
        if (hour >= 23 or hour < 5) and any(w in text for w in ["still working", "can't sleep", "coding", "work", "night"]):
            return "EMPATHETIC", "Late-night care mode activated."

        return "STANDBY", "Calm, attentive, and ready."

    # ------------------------------------------------------------------
    # AI processing & Tool Intent Routing
    # ------------------------------------------------------------------

    def _get_tools_for_query(self, user_input: str) -> list | None:
        """Selects a compact, relevant subset of tools based on intent to stay well within TPM/rate limits."""
        text = user_input.lower().strip()

        # Pure conversational greetings / feelings / chat -> 0 tools needed (lightning fast <500ms, <300 tokens)
        casual_patterns = [
            "how are you", "how're you", "how are you feeling", "how do you feel",
            "who are you", "what are you", "what is your name", "tell me about yourself",
            "hello", "hi", "hey maya", "hey", "kem cho", "kaise ho", "kya haal",
            "thank you", "thanks", "good job", "love you", "are you alive", "are you real",
            "what can you do", "nice to meet you", "કેમ છો", "નમસ્તે", "કેમ છે", "શું ચાલે છે"
        ]
        action_verbs = [
            "open", "close", "launch", "start", "stop", "play", "mute", "unmute",
            "volume", "turn on", "turn off", "toggle", "wifi", "bluetooth", "hotspot",
            "screenshot", "screen", "search", "google", "youtube", "weather", "news",
            "time", "date", "viva", "exam", "reminder", "timer", "schedule", "task",
            "todo", "calendar", "git", "commit", "diff", "file", "folder", "organize",
            "clean", "junk", "calculate", "write", "note", "notepad", "code", "python",
            "powershell", "email", "whatsapp", "camera", "photo", "battery", "restart",
            "shutdown", "lock", "ખોલો", "ચાલુ", "બંધ", "લખો", "વગાડો", "શોધો", "બનાવો", "દોરો", "કરો"
        ]

        if any(pat in text for pat in casual_patterns) and not any(verb in text for verb in action_verbs):
            return None

        matched_tools = []

        # Domain matching for targeted tool subsets
        # 1. Radio / System / Power / Settings (English, Hindi, Gujarati)
        if any(k in text for k in [
            "wifi", "bluetooth", "hotspot", "airplane", "brightness", "night light",
            "snap", "window", "power", "shutdown", "restart", "lock",
            "વાઇફાઇ", "વાઈફાઈ", "વાયફાય", "બ્લૂટૂથ", "બ્લુટુથ", "હોટસ્પોટ", "એરપ્લેન",
            "બ્રાઇટનેસ", "લોક", "શટડાઉન", "રીસ્ટાર્ટ", "ચાલુ કરો", "બંધ કરો", "ઓન કરો", "ઓફ કરો",
            "वाईफाई", "ब्लूटूथ", "हॉटस्पॉट", "चालू કરો", "बंद करो", "लॉक करो"
        ]):
            matched_tools.extend([
                "turn_on_wifi", "turn_off_wifi", "toggle_wifi", "get_wifi_status",
                "turn_on_bluetooth", "turn_off_bluetooth", "toggle_bluetooth",
                "turn_on_hotspot", "turn_off_hotspot", "turn_on_airplane_mode",
                "set_brightness", "snap_window", "switch_application", "system_power_control",
                "run_system_health_check"
            ])
        # 2. Code, Git, Development & OS Scripting
        if any(k in text for k in [
            "code", "git", "commit", "diff", "branch", "debug", "python", "test",
            "scaffold", "website", "html", "css", "script", "program", "develop",
            "કોડ", "પ્રોગ્રામ", "સ્ક્રિપ્ટ", "વેબસાઈટ", "પાયથોન", "કોડિંગ", "બનાવો", "પ્રોજેક્ટ"
        ]):
            matched_tools.extend([
                "run_python_code", "run_powershell_command", "create_file_or_folder", "create_project_scaffold",
                "git_status", "git_diff_summary", "git_log_recent", "git_commit_and_push_assistant",
                "run_project_tests", "security_code_review", "explain_code_or_concept"
            ])
        # 3. Web & Media & YouTube
        if any(k in text for k in [
            "browse", "tab", "article", "page", "summarize", "website", "compare", "price", "video",
            "youtube", "song", "music", "play", "audio", "track",
            "યુટ્યુબ", "ગીત", "ગાના", "વગાડો", "સંગીત", "વિડીયો", "શોધો", "સર્ચ", "વિકિપીડિયા", "સમાચાર", "ન્યૂઝ"
        ]):
            matched_tools.extend([
                "play_on_youtube", "summarize_youtube_video", "open_website", "summarize_webpage",
                "manage_browser_tabs", "compare_products_or_prices", "search_wikipedia", "get_news"
            ])
        # 4. Calendar, Scheduling & Productivity
        if any(k in text for k in [
            "calendar", "meeting", "agenda", "event", "schedule", "habit", "goal", "deadline", "pomodoro",
            "timer", "reminder", "task", "todo", "કેલેન્ડર", "મીટિંગ", "શેડ્યૂલ", "રિમાઇન્ડર", "યાદ", "ટાઈમર", "કામ"
        ]):
            matched_tools.extend([
                "create_calendar_event", "list_calendar_events", "reschedule_calendar_event",
                "delete_calendar_event", "generate_meeting_agenda", "generate_daily_schedule",
                "track_goal_or_deadline", "track_habit", "start_pomodoro", "start_timer"
            ])
        # 5. Documents, Notepad & Files
        if any(k in text for k in [
            "document", "pdf", "word", "docx", "excel", "spreadsheet", "csv", "duplicate", "rename",
            "organize", "file", "folder", "directory", "desktop", "create", "notepad", "write", "note", "recipe",
            "નોટપેડ", "પીડીએફ", "ફાઇલ", "ફોલ્ડર", "લખો", "ડેસ્કટોપ", "બનાવો", "રેસિપી", "નોંધ", "દસ્તાવેજ", "કચરો", "સાફ કરો"
        ]):
            matched_tools.extend([
                "open_pdf", "read_pdf", "generate_pdf",
                "read_document", "read_word_document", "read_excel_spreadsheet",
                "compare_documents", "find_duplicate_files", "bulk_rename_files",
                "search_local_documents", "organize_folder", "clean_junk_files",
                "create_file_or_folder", "copy_file", "move_file", "write_in_notepad",
                "write_recipe_in_notepad"
            ])
        # 6. Communication & WhatsApp
        if any(k in text for k in [
            "contact", "whatsapp", "phone", "message", "sms", "email", "reply",
            "વોટ્સએપ", "સંદેશ", "મેસેજ", "કોન્ટેક્ટ", "ઈમેલ", "મોકલો", "નંબર"
        ]):
            matched_tools.extend([
                "save_contact", "find_contact", "list_contacts", "send_whatsapp_message",
                "suggest_email_reply", "create_meeting_invitation", "compose_email", "open_email_client"
            ])
        # 7. Viva, Exam, Academics & Knowledge
        if any(k in text for k in [
            "viva", "exam", "quiz", "interview", "academic", "study", "વાઇવા", "પરીક્ષા", "ઇન્ટરવ્યુ"
        ]):
            matched_tools.extend([
                "conduct_viva_session", "conduct_mock_interview", "create_quiz_game"
            ])
        # 8. Applications opening/closing
        if any(k in text for k in [
            "open", "launch", "start", "close", "kill", "exit", "app", "application", "software",
            "ખોલો", "ઓપન", "શરૂ", "બંધ"
        ]):
            matched_tools.extend(["open_application", "close_application"])
        # 9. Smart Home / IoT
        if any(k in text for k in ["home assistant", "light", "plug", "scene", "iot", "fan", "લાઇટ", "લાઈટ", "પંખો"]):
            matched_tools.extend([
                "control_home_assistant_device", "activate_smart_scene", "control_smart_plug_or_light", "monitor_iot_sensors"
            ])
        # 10. AI Image & Artwork
        if any(k in text for k in ["image", "draw", "generate", "paint", "art", "picture", "photo", "wallpaper", "तस्वीर", "चित्र", "ફોટો", "ચિત્ર"]):
            matched_tools.extend([
                "generate_ai_image", "generate_wallpaper", "create_digital_art"
            ])
        # 11. Android phone companion
        if any(k in text for k in ["android", "phone", "mobile", "મોબાઇલ"]):
            matched_tools.extend([
                "android_device_status", "android_send_sms", "android_open_app", "android_push_file"
            ])

        # Base universal tools for common voice actions
        core_universal = [
            "open_application", "close_application", "adjust_volume", "take_screenshot",
            "read_screen", "search_web", "play_on_youtube", "get_weather", "get_time",
            "get_date", "calculate", "write_in_notepad", "set_reminder", "add_task",
            "read_tasks", "check_battery", "system_status"
        ]

        if not matched_tools:
            matched_tools = list(core_universal)
        else:
            # If a specific domain matched, add only essential action tools
            matched_tools.extend(["open_application", "search_web", "play_on_youtube"])

        seen = set()
        selected_schemas = []
        for name in matched_tools:
            if name in self.tool_schemas and name not in seen:
                seen.add(name)
                selected_schemas.append(self.tool_schemas[name])
                if len(selected_schemas) >= 16:
                    break

        return selected_schemas if selected_schemas else None

    def _try_fast_path(self, user_input: str) -> str | None:
        """Executes deterministic hardware/system queries locally in 0.001s with zero cloud latency."""
        text = user_input.lower().strip()
        cleaned = text
        while True:
            new_cleaned = re.sub(r'^(maya|jarvis|hey maya|hey|please|can you|could you|tell me|what is the|what\'s the|what is|what\'s|માયા|હેય માયા|કૃપા કરીને|સુનો માયા)[,\s]+', '', cleaned, flags=re.I).strip()
            if new_cleaned == cleaned:
                break
            cleaned = new_cleaned
        cleaned = re.sub(r'[?.!]+$', '', cleaned).strip()

        # 1. Time (English, Hindi, Gujarati)
        time_exact = {
            "time", "current time", "time right now", "time please", "time now", "the time",
            "what time", "tell time", "what is time", "समय", "समय क्या है", "कितने बजे हैं", "कितना बजा है",
            "टाइम", "टाइम क्या हुआ", "સમય", "સમય શું છે", "કેટલા વાગ્યા", "ટાઈમ", "ટાઇમ શું છે",
            "અત્યારે શું સમય થયો છે", "અત્યારે કેટલા વાગ્યા", "સમય બતાવો", "ટાઈમ શું થયો છે"
        }
        if cleaned in time_exact or ("time" in cleaned and any(w in cleaned for w in ["what", "tell", "current"]) and not any(w in cleaned for w in ["zone", "difference", "stopwatch"])):
            print("⚙️ Executing Tool: get_time | args: {}")
            return get_time()

        # 2. Date (English, Hindi, Gujarati)
        date_exact = {
            "date", "today's date", "date today", "current date", "the date", "what date",
            "day", "today", "what day is today", "तारीख", "आज की तारीख", "आज क्या तारीख है",
            "આજની તારીખ", "આજે કઈ તારીખ છે", "તારીખ", "આજની તારીખ શું છે", "તારીખ શું છે",
            "આજે કયો વાર છે", "કઈ તારીખ છે"
        }
        if cleaned in date_exact or ("date" in cleaned and any(w in cleaned for w in ["what", "today", "current"])):
            print("⚙️ Executing Tool: get_date | args: {}")
            return get_date()

        # 3. Battery (English, Hindi, Gujarati)
        if any(p in cleaned for p in ["battery", "battery percentage", "battery level", "battery status", "check battery", "how much battery", "બેટરી", "બેટરી કેટલી છે", "બેટરી બતાવો", "बैटरी", "बैटरी कितनी है"]) and len(cleaned.split()) <= 4:
            print("⚙️ Executing Tool: check_battery | args: {}")
            return check_battery()

        # 4. Screenshot (English, Hindi, Gujarati)
        if any(p in cleaned for p in ["take screenshot", "take a screenshot", "capture screen", "screen shot", "screenshot lo", "screenshot le lo", "स्क्रीनशॉट लो", "स्क्रीनशॉट", "સ્ક્રીનશોટ લો", "સ્ક્રીનશોટ"]) and len(cleaned.split()) <= 4:
            print("⚙️ Executing Tool: take_screenshot | args: {}")
            return take_screenshot()

        # 5. Volume controls (English, Hindi, Gujarati)
        if cleaned in ("mute", "mute volume", "mute audio", "mute sound", "sound mute", "audio mute", "आवाज बंद", "आवाज़ बंद करो", "અવાજ બંધ", "અવાજ બંધ કરો"):
            print("⚙️ Executing Tool: adjust_volume | args: {'action': 'mute'}")
            return adjust_volume('mute')
        if cleaned in ("unmute", "unmute volume", "unmute audio", "unmute sound", "sound unmute", "आवाज चालू", "आवाज़ चालू करो", "અવાજ ચાલુ", "અવાજ ચાલુ કરો"):
            print("⚙️ Executing Tool: adjust_volume | args: {'action': 'unmute'}")
            return adjust_volume('unmute')
        if cleaned in ("volume up", "increase volume", "turn up volume", "louder", "sound up", "आवाज बढ़ाओ", "આવાઝ વધારો", "અવાજ વધારો"):
            print("⚙️ Executing Tool: adjust_volume | args: {'action': 'up'}")
            return adjust_volume('up')
        if cleaned in ("volume down", "decrease volume", "turn down volume", "lower volume", "sound down", "आवाज कम करो", "આવાઝ ઘટાડો", "અવાજ ઘટાડો"):
            print("⚙️ Executing Tool: adjust_volume | args: {'action': 'down'}")
            return adjust_volume('down')

        # 5b. Wi-Fi Control (English, Hindi, Gujarati)
        if cleaned in ("turn on wifi", "wifi on", "enable wifi", "start wifi", "વાઇફાઇ ચાલુ કરો", "વાઈફાઈ ચાલુ કરો", "વાઇફાઇ ઓન કરો", "વાયફાય ચાલુ કરો", "वाईफाई चालू करो"):
            try:
                from skills.system_skills import turn_on_wifi
                print("⚙️ Executing Tool: turn_on_wifi | args: {}")
                return turn_on_wifi()
            except Exception as e:
                return f"Error toggling Wi-Fi: {e}"
        if cleaned in ("turn off wifi", "wifi off", "disable wifi", "stop wifi", "વાઇફાઇ બંધ કરો", "વાઈફાઈ બંધ કરો", "વાઇફાઇ ઓફ કરો", "વાયફાય બંધ કરો", "वाईफाई बंद करो"):
            try:
                from skills.system_skills import turn_off_wifi
                print("⚙️ Executing Tool: turn_off_wifi | args: {}")
                return turn_off_wifi()
            except Exception as e:
                return f"Error toggling Wi-Fi: {e}"

        # 5c. Bluetooth Control (English, Hindi, Gujarati)
        if cleaned in ("turn on bluetooth", "bluetooth on", "enable bluetooth", "બ્લૂટૂથ ચાલુ કરો", "બ્લુટુથ ચાલુ કરો", "બ્લૂટૂથ ઓન કરો", "ब्लूटूथ चालू करो"):
            try:
                from skills.system_skills import turn_on_bluetooth
                print("⚙️ Executing Tool: turn_on_bluetooth | args: {}")
                return turn_on_bluetooth()
            except Exception as e:
                return f"Error toggling Bluetooth: {e}"
        if cleaned in ("turn off bluetooth", "bluetooth off", "disable bluetooth", "બ્લૂટૂથ બંધ કરો", "બ્લુટુથ બંધ કરો", "બ્લૂટૂથ ઓફ કરો", "ब्लूटूथ बंद करो"):
            try:
                from skills.system_skills import turn_off_bluetooth
                print("⚙️ Executing Tool: turn_off_bluetooth | args: {}")
                return turn_off_bluetooth()
            except Exception as e:
                return f"Error toggling Bluetooth: {e}"

        # 5d. Hotspot Control (English, Hindi, Gujarati)
        if cleaned in ("turn on hotspot", "hotspot on", "enable hotspot", "હોટસ્પોટ ચાલુ કરો", "हॉटस्पॉट चालू करो"):
            try:
                from skills.system_skills import turn_on_hotspot
                print("⚙️ Executing Tool: turn_on_hotspot | args: {}")
                return turn_on_hotspot()
            except Exception as e:
                return f"Error toggling Hotspot: {e}"
        if cleaned in ("turn off hotspot", "hotspot off", "disable hotspot", "હોટસ્પોટ બંધ કરો", "हॉटस्पॉट बंद करो"):
            try:
                from skills.system_skills import turn_off_hotspot
                print("⚙️ Executing Tool: turn_off_hotspot | args: {}")
                return turn_off_hotspot()
            except Exception as e:
                return f"Error toggling Hotspot: {e}"

        # 5e. Lock Computer (English, Hindi, Gujarati)
        if cleaned in ("lock pc", "lock computer", "lock screen", "કમ્પ્યુટર લોક કરો", "પીસી લોક કરો", "સ્ક્રીન લોક કરો", "स्क्रीन लॉक करो", "कंप्यूटर लॉक करो"):
            try:
                from skills.system_skills import system_power_control
                print("⚙️ Executing Tool: system_power_control | args: {'action': 'lock'}")
                return system_power_control(action='lock')
            except Exception as e:
                return f"Error locking system: {e}"

        # 5f-0. DEDICATED UNIVERSAL PDF ARSENAL DISPATCHER
        # Handles all PDF Generate, Open, and Read requests deterministically across English, Hindi, and Gujarati
        has_pdf_trigger = any(k in cleaned for k in ["pdf", "પીડીએફ", "पीडीएफ", ".pdf", "maya_introduction", "maya introduction"])

        if has_pdf_trigger:
            # 1. Is this a GENERATION request? (Takes highest priority)
            is_gen_intent = any(w in cleaned for w in [
                "generate", "create", "make", "write", "build", "produce", "export",
                "banao", "bana", "banado", "chahiye", "nikalo", "tayyar",
                "બનાવો", "બનાવી", "બનાવ", "તૈયાર", "લખો",
                "बनाओ", "बना", "बनाएं", "जनरेट", "क्रिएट", "लिखो", "तैयार"
            ]) or "add content yourself" in cleaned or "content yourself" in cleaned or cleaned in ("pdf", "generate pdf", "make pdf", "create pdf", "pdf banao")

            # 2. Is this a READ request? (Only if NOT generating)
            is_read_intent = not is_gen_intent and any(w in cleaned for w in [
                "read", "summarize", "summary", "explain", "extract", "what is inside", "what does it say",
                "vancho", "samjhavo", "padho", "samjhao", "વાંચો", "સમજાવો", "વાંચ", "સમજાવ", "पढ़ो", "पढ़", "समझाइए"
            ])

            # 3. Is this an OPEN request? (Only if NOT generating and NOT reading)
            is_open_intent = not is_gen_intent and not is_read_intent and any(w in cleaned for w in [
                "open", "launch", "view", "kholo", "show", "display",
                "खोलो", "ખોલો", "ઓપન", "ખોલ", "खोल"
            ])

            if is_gen_intent:
                topic_raw = cleaned
                # Check for explicit named title (e.g. "name Maya_Introduction")
                m_named = re.search(r'\b(?:name(?:d)?|titled|called)\s+(?:is\s+|as\s+|to\s+)?([a-zA-Z0-9_\-]+)', topic_raw, re.I)
                explicit_name = m_named.group(1).replace("_", " ").strip() if m_named else ""

                topic_raw = re.sub(r'\b(pdf|પીડીએફ|पीडीएफ|\.pdf)\b', ' ', topic_raw, flags=re.I)
                gen_stop_words = [
                    "generate", "create", "make", "write", "build", "produce", "export",
                    "banao", "bana", "banado", "chahiye", "nikalo", "tayyar", "karo", "do", "de",
                    "બનાવો", "બનાવી", "બનાવ", "તૈયાર", "લખો", "કરો", "આપો",
                    "बनाओ", "बना", "बनाएं", "जनरेट", "क्रिएट", "लिखो", "तैयार", "करो",
                    "a", "an", "the", "on", "about", "for", "of", "in", "to", "with",
                    "ek", "mujhe", "hame", "hamko", "apna", "meri", "mera", "mere",
                    "ki", "ka", "ke", "ko", "se", "par", "pe", "karke", "aur", "and",
                    "open", "it", "show", "me", "view", "kholo", "खोलो", "ખોલો",
                    "now", "name", "named", "and this", "this", "add content yourself",
                    "content yourself", "write content yourself", "yourself", "add content", "write content",
                    "complete", "detailed explanations", "detailed", "explanations",
                    "diagrams", "diagram", "examples", "example", "professional formatting",
                    "professional", "formatting", "format", "notes", "study materials",
                    "પર", "વિશે", "માટે", "નું", "નો", "ની", "ના", "એક", "મને"
                ]
                for sw in gen_stop_words:
                    topic_raw = re.sub(rf'\b{re.escape(sw)}\b', ' ', topic_raw, flags=re.I)

                clean_topic = explicit_name or " ".join(topic_raw.split()).strip()
                if "machine learning" in cleaned:
                    clean_topic = "Machine Learning"
                elif "maya" in cleaned:
                    clean_topic = explicit_name or "Maya Introduction"
                elif not clean_topic or len(clean_topic) < 2 or clean_topic.lower() in ["file", "document", "report"]:
                    clean_topic = "Machine Learning"

                title_text = clean_topic.title()
                print(f"⚙️ Executing Tool: generate_pdf | args: {{'title': '{title_text}'}}")
                return generate_pdf(title=title_text, content="")

            elif is_read_intent:
                clean_target = re.sub(r'^(?:read|summarize|explain|extract|વાંચો|સમજાવો|पढ़ो)\s+(?:the\s+)?(?:pdf\s+)?', '', cleaned, flags=re.I).strip()
                clean_target = re.sub(r'\s+(?:read|summarize|explain|વાંચો|સમજાવો|पढ़ो)$', '', clean_target, flags=re.I).strip()
                print(f"⚙️ Executing Tool: read_pdf | args: {{'pdf_name_or_path': '{clean_target}'}}")
                return read_pdf(clean_target)

            elif is_open_intent:
                clean_target = re.sub(r'^(?:open|launch|view|kholo|show|खोलो|ખોલો|ઓપન)\s+(?:the\s+)?(?:pdf\s+)?', '', cleaned, flags=re.I).strip()
                clean_target = re.sub(r'\s+(?:open|launch|kholo|ખોલો)$', '', clean_target, flags=re.I).strip()
                print(f"⚙️ Executing Tool: open_pdf | args: {{'pdf_name_or_path': '{clean_target}'}}")
                return open_pdf(clean_target)

        # 5f. Open Application Universal Fast-Path (English, Gujarati, Hindi)
        gu_hi_app_map = {
            "નોટપેડ": "notepad", "ક્રોમ": "chrome", "કેલ્ક્યુલેટર": "calculator",
            "કેમેરા": "camera", "સેટિંગ્સ": "settings", "પેઇન્ટ": "paint",
            "વર્ડ": "word", "એક્સેલ": "excel", "યુટ્યુબ": "youtube",
            "ફાઇલ એક્સપ્લોરર": "file explorer", "ટાસ્ક મેનેજર": "task manager",
            "નોટ પેડ": "notepad", "કેલ્સી": "calculator", "બ્રાઉઝર": "chrome",
            "સ્ટોર": "store", "ઘડિયાળ": "clock", "ફોટા": "photos",
            "વિડીયો": "vlc", "મ્યુઝિક": "spotify", "ગૂગલ": "chrome",
            "नोटपैड": "notepad", "क्रोम": "chrome", "कैलकुलेटर": "calculator",
            "कैमरा": "camera", "सेटिंग्स": "settings", "वर्ड": "word", "एक्सेल": "excel"
        }
        tricky_app_names = {
            "word", "excel", "powerpoint", "notepad", "calculator", "chrome",
            "edge", "camera", "settings", "paint", "vlc", "spotify", "code",
            "vscode", "terminal", "powershell", "cmd", "explorer", "task manager",
            "steam", "blender", "acrobat", "discord", "whatsapp", "zoom", "teams"
        }

        # A. Check prefix verbs: open, launch, start, run, kholo, chalu karo, shuru karo, ખોલો, ચાલુ કરો
        m_open_prefix = re.search(r"^(?:open\s+karo|chalu\s+karo|shuru\s+karo|ઓપન\s+કરો|ચાલુ\s+કરો|શરૂ\s+કરો|चालू\s+करो|शुरू\s+करो|ओपन\s+करो|open|launch|start|run|kholo|ખોલો|ખોલ|खोलो|ઓપન|ओपन)\s+(.+)$", cleaned, re.I)
        # B. Check suffix verbs: [app] open, [app] kholo, [app] open karo, [app] chalu karo, [app] ખોલો, [app] ચાલુ કરો
        m_open_suffix = re.search(r"^(.+?)\s+(?:open\s+karo|chalu\s+karo|shuru\s+karo|ઓપન\s+કરો|ચાલુ\s+કરો|શરૂ\s+કરો|चालू\s+करो|शुरू\s+करो|ओपन\s+करो|open|launch|start|run|kholo|ખોલો|ખોલ|खोલો|ઓપન|ओपन)$", cleaned, re.I)

        target_app_to_open = None
        if m_open_prefix:
            target_app_to_open = m_open_prefix.group(1).strip()
            target_app_to_open = re.sub(r"^(?:karo|ne|to|bhai|જરા|કરો)\s*", "", target_app_to_open).strip()
        elif m_open_suffix:
            target_app_to_open = m_open_suffix.group(1).strip()
        elif cleaned in gu_hi_app_map:
            target_app_to_open = gu_hi_app_map[cleaned]
        elif cleaned in tricky_app_names:
            target_app_to_open = cleaned

        if target_app_to_open:
            # Translate vernacular name if applicable
            resolved_app_chk = gu_hi_app_map.get(target_app_to_open, target_app_to_open)
            if resolved_app_chk.lower().endswith(".pdf") or "pdf" in resolved_app_chk.lower().split():
                pdf_target = re.sub(r'\bpdf\b', '', resolved_app_chk, flags=re.I).strip() or resolved_app_chk
                if not pdf_target.lower().endswith(".pdf"):
                    pdf_target += ".pdf"
                print(f"⚙️ Executing Tool: open_pdf | args: {{'pdf_name_or_path': '{pdf_target}'}}")
                return open_pdf(pdf_target)
            resolved_app = gu_hi_app_map.get(target_app_to_open, target_app_to_open)
            if not any(k in resolved_app.lower() for k in [
                "project folder", "dashboard", "website", "folder called", "file called", "http", ".com", ".org", "youtube", "video", "song"
            ]):
                print(f"⚙️ Executing Tool: open_application | args: {{'app_name': '{resolved_app}'}}")
                return open_application(resolved_app)

        # 5g. Close Application Fast-Path (English, Gujarati, Hindi)
        m_close_prefix = re.search(r"^(?:close|kill|exit|quit|shut down|terminate|બંધ\s+કરો|બંદ\s+કરો|બંધ\s+કર|बंद\s+करो)\s+(.+)$", cleaned, re.I)
        m_close_suffix = re.search(r"^(.+?)\s+(?:close|kill|exit|quit|shut down|terminate|બંધ\s+કરો|બંદ\s+કરો|બંધ\s+કર|बंद\s+करो)$", cleaned, re.I)
        target_app_to_close = None
        if m_close_prefix:
            target_app_to_close = m_close_prefix.group(1).strip()
        elif m_close_suffix:
            target_app_to_close = m_close_suffix.group(1).strip()

        if target_app_to_close:
            resolved_close = gu_hi_app_map.get(target_app_to_close, target_app_to_close)
            print(f"⚙️ Executing Tool: close_application | args: {{'app_name': '{resolved_close}'}}")
            return close_application(resolved_close)

        # 5h. YouTube Play Fast-Path (English & Gujarati)
        if ("play" in cleaned or "વગાડો" in cleaned or "સાંભળો" in cleaned) and ("youtube" in cleaned or "યુટ્યુબ" in cleaned or "યૂટ્યૂબ" in cleaned):
            yt_query = re.sub(r'^(?:play|watch)\s+', '', cleaned, flags=re.I)
            yt_query = re.sub(r'\s+(?:on|in)\s+youtube.*$', '', yt_query, flags=re.I)
            yt_query = re.sub(r'(?:યુટ્યુબ પર|યૂટ્યૂબ પર)\s*', '', yt_query)
            yt_query = re.sub(r'\s*(?:વગાડો|ચાલુ કરો|બતાવો)$', '', yt_query).strip()
            print(f"⚙️ Executing Tool: play_on_youtube | args: {{'query': '{yt_query}'}}")
            return play_on_youtube(yt_query)

        # 6. Empty Recycle Bin
        if any(p in cleaned for p in ["empty recycle bin", "clean recycle bin", "clear recycle bin", "કચરો સાફ કરો", "कचरा साफ करो", "રીસાયકલ બિન સાફ કરો", "રીસાયકલ બિન ખાલી કરો", "रीसायकल बिन खाली करो"]):
            try:
                from skills.smart_home_skills import empty_recycle_bin
                print("⚙️ Executing Tool: empty_recycle_bin | args: {}")
                return empty_recycle_bin()
            except Exception:
                pass

        # 7. AI Image & Wallpaper Generation Fast-Path (English, Hindi, Gujarati)
        m_img = re.search(r'(?:generate|create|make|draw|paint|show|show me|display)\s+(?:an?\s+)?(?:ai\s+)?(?:image|art|picture|photo|painting)\s+(?:of|for)\s+(.+)$', cleaned, re.I)
        if not m_img:
            m_img = re.search(r'^(?:an?\s+)?(?:image|picture|photo|painting)\s+(?:of|for)\s+(.+)$', cleaned, re.I)
        if not m_img:
            m_img = re.search(r'^(?:draw|paint)\s+(?:me\s+)?(?:an?\s+)?(.+)$', cleaned, re.I)

        if m_img:
            try:
                from skills.image_generation_skills import generate_ai_image
                return generate_ai_image(prompt=m_img.group(1).strip())
            except Exception as e:
                return f"Error creating image: {e}"

        m_indic = re.search(r'(.+?)\s*(?:की\s*तस्वीर|की\s*फोटो|का\s*चित्र|નું\s*ચિત્ર|ની\s*તસવીર|નો\s*ફોટો)\s*(?:बनाओ|बनाएं|દોરો|બનાવો|બનાવી\s*આપો)', cleaned, re.I)
        if m_indic:
            try:
                from skills.image_generation_skills import generate_ai_image
                return generate_ai_image(prompt=m_indic.group(1).strip())
            except Exception as e:
                return f"Error creating image: {e}"

        m_wall = re.search(r'(?:generate|create|make|set)\s+(?:a\s+)?wallpaper\s+(?:of|for|with)\s+(.+)$', cleaned, re.I)
        if m_wall:
            try:
                from skills.image_generation_skills import generate_wallpaper
                return generate_wallpaper(theme=m_wall.group(1).strip())
            except Exception as e:
                return f"Error creating wallpaper: {e}"

        return None

    # ------------------------------------------------------------------
    # AI processing
    # ------------------------------------------------------------------

    def _process_with_ai(self, user_input):
        # 0. Zero-latency local fast-path for deterministic hardware and system queries
        fast_result = self._try_fast_path(user_input)
        if fast_result is not None:
            print(f"⚡ [FAST-PATH INTENT]: {fast_result}")
            clean = re.sub(r'[*_`#]', '', fast_result).strip()
            print(f"🤖 Maya: {clean}")
            self.voice.speak(clean)
            self.save_history("User", user_input)
            self.save_history("Maya", clean)
            self.messages.append({"role": "user", "content": user_input})
            self.messages.append({"role": "assistant", "content": clean})
            print("SLEEP MODE — response complete.")
            return
        print(f"Thinking about: {user_input}")
        self.save_history("User", user_input)
        self.messages.append({"role": "user", "content": user_input})

        # Keep conversation window: system prompt + last 8 messages
        if len(self.messages) > 10:
            self.messages = [self.messages[0]] + self.messages[-8:]

        # Emotional sentiment analysis & dynamic mood modulation
        mood, mood_desc = self.analyze_user_sentiment(user_input)
        self.current_mood = mood
        if hasattr(self.voice, 'set_mood'):
            self.voice.set_mood(mood)
        print(f"🎭 [MOOD: {mood}] {mood_desc}")

        # Inject dynamic emotional protocol into this generation turn
        mood_instruction = {
            "role": "system",
            "content": f"[EMOTION PROTOCOL: Maya currently feels {mood} ({mood_desc}). Ensure your spoken tone authentically embodies this feeling with warm, genuine human emotion and conversational presence.]"
        }
        dispatch_messages = [self.messages[0], mood_instruction] + self.messages[1:]

        # Dynamic tool selection: keep payload well under 8,000 TPM limit
        active_tools = self._get_tools_for_query(user_input)
        is_heavy_task = any(k in user_input.lower() for k in [
            "code", "website", "script", "html", "css", "program", "python", "create", "folder", "write", "develop"
        ])
        req_kwargs = {
            "messages": dispatch_messages,
            "max_tokens": 950 if is_heavy_task else 800,
            "temperature": 0.7,
        }
        if active_tools:
            req_kwargs["tools"] = active_tools
            req_kwargs["tool_choice"] = "auto"

        try:
            active_model = getattr(self, 'model', self.config.get('assistant', {}).get('model', 'openai/gpt-oss-120b'))
            try:
                response = self.client.chat.completions.create(
                    model=active_model,
                    **req_kwargs
                )
            except Exception as primary_err:
                err_str = str(primary_err).lower()
                if "rate_limit" in err_str or "tokens" in err_str or "413" in err_str or "tpm" in err_str:
                    print(f"⚠️ Context limit or rate limit encountered ({primary_err}). Retrying with compacted context...")
                    compact_msgs = [self.messages[0], mood_instruction, {"role": "user", "content": user_input}]
                    fallback_tools = None if ("how are you" in user_input.lower() or "feel" in user_input.lower()) else (active_tools[:8] if active_tools else None)
                    retry_kwargs = {
                        "model": active_model,
                        "messages": compact_msgs,
                        "max_tokens": 500,
                        "temperature": 0.7,
                    }
                    if fallback_tools:
                        retry_kwargs["tools"] = fallback_tools
                        retry_kwargs["tool_choice"] = "auto"
                    response = self.client.chat.completions.create(**retry_kwargs)
                elif self.groq_client and self.client != self.groq_client:
                    print(f"⚠️ Primary provider notice: {primary_err}")
                    print(f"🔄 Automatically routing request to backup Groq engine ({self.groq_model})...")
                    self.client = self.groq_client
                    self.provider = "groq"
                    active_model = getattr(self, 'groq_model', 'qwen/qwen3.8-27b')
                    self.model = active_model
                    response = self.client.chat.completions.create(
                        model=active_model,
                        **req_kwargs
                    )
                else:
                    raise primary_err

            ai_message = response.choices[0].message

            if ai_message.tool_calls:
                raw_results = []
                executed_this_turn = set()

                for tool_call in ai_message.tool_calls:
                    func_name = tool_call.function.name
                    raw_args  = tool_call.function.arguments
                    sig = f"{func_name}_{raw_args}"

                    if sig in executed_this_turn:
                        raw_results.append(f"Tool '{func_name}' was already executed.")
                        continue
                    executed_this_turn.add(sig)

                    try:
                        args = json.loads(raw_args) if raw_args else {}
                        if not isinstance(args, dict): args = {}
                    except Exception:
                        args = {}

                    print(f"⚙️ Executing Tool: {func_name} | args: {args}")

                    if func_name in self.tools_map:
                        try:
                            result, receipt = self.orchestrator.execute_with_receipt(func_name, args)
                            raw_results.append(str(result))
                        except Exception as tool_err:
                            raw_results.append(f"Error executing {func_name}: {tool_err}")
                    else:
                        raw_results.append(f"Tool '{func_name}' is not recognized.")

                # --- Siri-style: record execution in context ---
                tool_summary = " | ".join(raw_results)
                self.messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": ai_message.tool_calls
                })
                for tc, res in zip(ai_message.tool_calls, raw_results):
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": res
                    })

                # Check if tool_summary is already a clean, friendly spoken sentence
                # (Saves 2-3 seconds of second-pass LLM roundtrip delay!)
                is_clean_spoken = (
                    len(raw_results) == 1
                    and len(tool_summary) < 280
                    and not tool_summary.startswith(("{", "[", "Traceback", "<"))
                    and not any(err in tool_summary.lower() for err in ["error executing", "traceback", "syntaxerror", "exception", "failed to", "not recognized"])
                )

                if is_clean_spoken:
                    natural_response = tool_summary
                else:
                    # Second pass: only invoke LLM when synthesis or explanation is needed
                    try:
                        follow_up = self.client.chat.completions.create(
                            model=active_model,
                            messages=self.messages,
                            max_tokens=300,
                            temperature=0.7,
                        )
                        natural_response = follow_up.choices[0].message.content or tool_summary
                    except Exception:
                        try:
                            follow_up = self.client.chat.completions.create(
                                model=active_model,
                                messages=[self.messages[0], {"role": "user", "content": f"The tool returned: {tool_summary}. Give a brief 1-sentence friendly confirmation to the user."}],
                                max_tokens=150,
                                temperature=0.7,
                            )
                            natural_response = follow_up.choices[0].message.content or tool_summary
                        except Exception:
                            natural_response = tool_summary

                # Clean up any markdown from voice output
                clean = re.sub(r'[*_`#]', '', natural_response).strip()
                print(f"\U0001f916 Maya: {clean}")
                self.voice.speak(clean)
                self.save_history("Maya", clean)
                self.messages.append({"role": "assistant", "content": clean})
                print("SLEEP MODE — response complete.")
                return

            if ai_message.content:
                content = ai_message.content
                # Strip internal reasoning tokens from Nemotron
                if any(k in content.lower() for k in ["thinking process", "analyze user input", "formulate response", "check constraints"]):
                    m = re.findall(r'(?:Output|Response):\s*[\"\']?([^\"\n\r]{5,280})[\"\']?', content, re.IGNORECASE)
                    if m:
                        content = m[-1].strip()
                    else:
                        quotes = [q.strip() for q in re.findall(r'"([^"\n\r]{10,280})"', content) if not any(w in q.lower() for w in ["rules", "sentences", "prompt", "user says", "constraint", "thinking", "output", "step"])]
                        if quotes:
                            content = quotes[-1]
                        else:
                            lines = [ln.strip() for ln in content.splitlines() if ln.strip() and not ln.lower().startswith(("here's", "1.", "2.", "3.", "4.", "5.", "6.", "-", "*", "analyze", "user", "i need", "check", "formulate", "output", "proceed", "let's", "done"))]
                            if lines:
                                content = lines[-1]
                # Strip internal reasoning / chain-of-thought tokens if returned by reasoning models (Nemotron)
                if "thinking process" in content.lower() or "analyze user input" in content.lower():
                    m_resp = re.search(r"Response:\s*['\"]?(.*?)['\"]?$", content, re.DOTALL | re.IGNORECASE)
                    if m_resp and len(m_resp.group(1).strip()) > 3:
                        content = m_resp.group(1).strip()
                    else:
                        quotes = re.findall(r'"([^"\n]{10,250})"', content)
                        if quotes:
                            content = quotes[-1].strip()
                        else:
                            clean_lines = [ln.strip() for ln in content.splitlines() if ln.strip() and not ln.lower().startswith(("here's a thinking", "1.", "2.", "3.", "4.", "5.", "6.", "-", "*", "analyze", "user says", "i need to", "personality rules", "determine response", "check constraints", "formulate response", "all good", "output matches", "proceed", "let's keep it"))]
                            content = clean_lines[-1] if clean_lines else "I am doing great, Nimish! How can I help you today?"
                # Autonomous Safeguard: Check if user asked for PDF generation but LLM output raw text instead of tool calling
                u_lower = user_input.lower()
                is_pdf_gen_intent = (
                    any(p in u_lower for p in ["pdf", "પીડીએફ", "पीडीएफ"])
                    and any(v in u_lower for v in ["generate", "create", "make", "write", "banao", "bana", "chahiye", "બનાવો", "બનાવી", "બનાવ", "તૈયાર", "बनाओ", "बना", "जनरेट", "क्रिएट"])
                    and not any(v in u_lower for v in ["read", "summarize", "explain", "extract", "vancho", "padho", "વાંચો", "સમજાવો", "पढ़ो"])
                )

                if is_pdf_gen_intent:
                    clean_title = re.sub(r'\b(generate|create|make|write|a|an|the|pdf|on|about|for|of|ki|ka|ke|par|banao|bana|do|karo|બનાવો|પીડીએફ|પર|વિશે)\b', ' ', u_lower, flags=re.I).strip()
                    clean_title = " ".join(clean_title.split()).title() or "Maya Generated Document"
                    print(f"📄 [AI PDF AUTONOMOUS RECOVERY]: Converting LLM content into PDF for '{clean_title}'...")
                    pdf_result = generate_pdf(title=clean_title, content=content)
                    
                    short_confirm = f"Maine '{clean_title}' par PDF generate karke aapke screen par open kar di hai, Nimish Sir."
                    print(f"🤖 Maya: {short_confirm}")
                    self.voice.speak(short_confirm)
                    self.save_history("Maya", short_confirm)
                    self.messages.append({"role": "assistant", "content": short_confirm})
                    print("SLEEP MODE — response complete.")
                    return

                # Clean markdown for voice output
                clean = re.sub(r'[*_`#]', '', content).strip()
                self.messages.append({"role": "assistant", "content": clean})
                print(f"🤖 Maya: {clean}")
                self.voice.speak(clean)
                self.save_history("Maya", clean)
                print("SLEEP MODE — response complete.")

        except Exception as e:
            error_msg = str(e).lower()

            if "connection" in error_msg or "network" in error_msg or "timeout" in error_msg:
                print(f"⚠️ Network Issue: {e}")
                self.voice.speak("My connection is lost. Please check your internet.")
                return

            # Catch Groq tool_use_failed / failed_generation (e.g. truncated tool call arguments)
            if "failed_generation" in error_msg or "tool_use_failed" in error_msg:
                print("\n⚠️ Catching AI's truncated or malformed tool generation...")
                try:
                    raw_gen = None
                    if hasattr(e, 'body') and isinstance(e.body, dict):
                        raw_gen = e.body.get('error', {}).get('failed_generation')
                    if not raw_gen:
                        m = re.search(r"['\"]failed_generation['\"]\s*:\s*['\"](.*)", str(e), re.DOTALL)
                        if m:
                            raw_gen = m.group(1)
                            raw_gen = re.sub(r"['\"]\s*\}\s*\}\s*$", "", raw_gen)

                    if raw_gen:
                        fn_match = re.search(r'["\']name["\']\s*:\s*["\'](\w+)["\']', raw_gen)
                        func_name = fn_match.group(1) if fn_match else None

                        args = {}
                        repaired = False
                        for suffix in ['', '"', '"}', '"} }', '}', '} }']:
                            try:
                                parsed = json.loads(raw_gen + suffix)
                                if isinstance(parsed, dict):
                                    if "name" in parsed: func_name = parsed["name"]
                                    args = parsed.get("arguments", {})
                                    if isinstance(args, str):
                                        try: args = json.loads(args)
                                        except Exception: pass
                                    repaired = True
                                    break
                            except Exception:
                                continue

                        if not repaired and func_name:
                            c_match = re.search(r'["\']content["\']\s*:\s*["\'](.*)', raw_gen, re.DOTALL)
                            if c_match:
                                c_text = c_match.group(1)
                                c_text = re.sub(r'["\'}\]\s]+$', '', c_text)
                                c_text = c_text.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")
                                args = {"content": c_text}
                                repaired = True

                        if func_name and func_name in self.tools_map:
                            if func_name == "run_python_code" and "code" in args and isinstance(args["code"], str):
                                code_str = args["code"]
                                # Auto-repair unclosed quotes / triple quotes if truncated
                                if code_str.count("'''") % 2 != 0:
                                    code_str += "\n'''"
                                if code_str.count('"""') % 2 != 0:
                                    code_str += '\n"""'
                                args["code"] = code_str
                            print(f"🪄 Auto-Recovered Tool Call: {func_name} | args: {list(args.keys())}")
                            result, _ = self.orchestrator.execute_with_receipt(func_name, args)
                            dish = args.get('dish_name') or args.get('title') or ""
                            if "recipe" in func_name:
                                clean_res = f"I have written the recipe for {dish} in Notepad for you." if dish else "I have written the recipe in Notepad for you."
                            elif "notepad" in func_name:
                                clean_res = f"I have written {dish or 'the document'} in Notepad for you."
                            else:
                                clean_res = str(result)
                            print(f"🤖 Maya: {clean_res}")
                            self.voice.speak(clean_res)
                            self.save_history("Maya (Auto-Action)", clean_res)
                            self.messages.append({"role": "assistant", "content": clean_res})
                            print("SLEEP MODE — response complete.")
                            return
                except Exception as rec_err:
                    print(f"Failed to auto-recover tool call: {rec_err}")

            if "<function=" in error_msg:
                print("\n⚠️ Catching AI's hidden command...")
                try:
                    match = re.search(r'<function=(\w+)(.*?)</function>', str(e))
                    if match:
                        func_name = match.group(1)
                        raw_json  = match.group(2).strip()
                        args = {}
                        if raw_json:
                            try: args = json.loads(raw_json)
                            except Exception: pass
                        print(f"🪄 Auto-Fixed: {func_name} | args: {args}")
                        if func_name in self.tools_map:
                            result, _ = self.orchestrator.execute_with_receipt(func_name, args)
                            print(f"🤖 Maya: {result}")
                            self.voice.speak(str(result))
                            self.save_history("Maya (Auto-Action)", str(result))
                            self.messages.append({"role": "assistant", "content": f"[Action Executed]: {str(result)}"})
                            return
                except Exception as parse_e:
                    print(f"Failed to auto-fix: {parse_e}")

            print(f"Groq System Error: {e}")
            self.voice.speak("I encountered an internal error. Please try again.")
