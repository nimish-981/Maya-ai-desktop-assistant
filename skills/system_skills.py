"""
skills/system_skills.py

System-level info and control tools: time, date, real hardware metrics,
clipboard access, reminder timers, and native Windows laptop controls
(Bluetooth, Wi-Fi, Mobile Hotspot, Airplane Mode, Quick Settings).
These functions are auto-registered as Groq tools via engine.py.
"""
import asyncio
import os
import subprocess
import time
from datetime import datetime


# =====================================================================
# Internal Async Helper for Windows Runtime APIs
# =====================================================================

def _run_coro_sync(coro, timeout: float = 8.0):
    """Safely runs an asyncio coroutine synchronously without blocking existing event loops."""
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result(timeout=timeout)
        else:
            return asyncio.run(coro)
    except Exception as e:
        raise e


# =====================================================================
# 1. BLUETOOTH CONTROL (Native Windows Device Radios API)
# =====================================================================

async def _async_set_bluetooth_state(target_state):
    from winrt.windows.devices.radios import Radio, RadioKind, RadioState
    access = await Radio.request_access_async()
    radios = await Radio.get_radios_async()
    for r in radios:
        if r.kind == RadioKind.BLUETOOTH:
            await r.set_state_async(target_state)
            return True, r.state
    return False, None


async def _async_get_bluetooth_state():
    from winrt.windows.devices.radios import Radio, RadioKind, RadioState
    radios = await Radio.get_radios_async()
    for r in radios:
        if r.kind == RadioKind.BLUETOOTH:
            return r.state
    return None


def turn_on_bluetooth() -> str:
    """Turns on the laptop's Bluetooth adapter. Use when the user says 'turn on bluetooth', 'enable bluetooth', or in Gujarati 'બ્લૂટૂથ ચાલુ કરો'."""
    try:
        from winrt.windows.devices.radios import RadioState
        found, state = _run_coro_sync(_async_set_bluetooth_state(RadioState.ON))
        if found:
            return "Bluetooth has been turned on."
        # Fallback if no radio object was found
        os.system("start ms-settings:bluetooth")
        return "I opened Bluetooth settings so you can switch it on."
    except Exception as e:
        try:
            os.system("start ms-settings:bluetooth")
            return "I opened Bluetooth settings for you to toggle Bluetooth on."
        except Exception:
            return f"Could not turn on Bluetooth: {e}"


def turn_off_bluetooth() -> str:
    """Turns off the laptop's Bluetooth adapter. Use when the user says 'turn off bluetooth', 'disable bluetooth', or in Gujarati 'બ્લૂટૂથ બંધ કરો'."""
    try:
        from winrt.windows.devices.radios import RadioState
        found, state = _run_coro_sync(_async_set_bluetooth_state(RadioState.OFF))
        if found:
            return "Bluetooth has been turned off."
        os.system("start ms-settings:bluetooth")
        return "I opened Bluetooth settings so you can switch it off."
    except Exception as e:
        try:
            os.system("start ms-settings:bluetooth")
            return "I opened Bluetooth settings for you to toggle Bluetooth off."
        except Exception:
            return f"Could not turn off Bluetooth: {e}"


def toggle_bluetooth() -> str:
    """Toggles the laptop's Bluetooth adapter on or off depending on current state."""
    try:
        from winrt.windows.devices.radios import RadioState
        curr = _run_coro_sync(_async_get_bluetooth_state())
        if curr == RadioState.ON:
            return turn_off_bluetooth()
        else:
            return turn_on_bluetooth()
    except Exception as e:
        os.system("start ms-settings:bluetooth")
        return f"Toggled Bluetooth settings ({e})."


def get_bluetooth_status() -> str:
    """Checks and returns the current status of the laptop's Bluetooth radio (On or Off)."""
    try:
        from winrt.windows.devices.radios import RadioState
        curr = _run_coro_sync(_async_get_bluetooth_state())
        if curr == RadioState.ON:
            return "Bluetooth is currently turned On."
        elif curr == RadioState.OFF:
            return "Bluetooth is currently turned Off."
        elif curr is None:
            return "No Bluetooth radio was detected on this computer."
        return f"Bluetooth is in state: {curr}."
    except Exception as e:
        return f"Could not check Bluetooth status: {e}"


def _open_bluetooth_settings() -> str:
    """Opens Windows Bluetooth & Devices Settings directly."""
    try:
        os.system("start ms-settings:bluetooth")
        return "Opened Windows Bluetooth settings."
    except Exception as e:
        return f"Could not open Bluetooth settings: {e}"


# =====================================================================
# 2. WI-FI CONTROL (Native Windows Device Radios API)
# =====================================================================

async def _async_set_wifi_state(target_state):
    from winrt.windows.devices.radios import Radio, RadioKind, RadioState
    access = await Radio.request_access_async()
    radios = await Radio.get_radios_async()
    for r in radios:
        if r.kind == RadioKind.WI_FI:
            await r.set_state_async(target_state)
            return True, r.state
    return False, None


async def _async_get_wifi_state():
    from winrt.windows.devices.radios import Radio, RadioKind, RadioState
    radios = await Radio.get_radios_async()
    for r in radios:
        if r.kind == RadioKind.WI_FI:
            return r.state
    return None


def turn_on_wifi() -> str:
    """Turns on the laptop's Wi-Fi adapter. Use when the user says 'turn on wifi', 'enable wifi', or 'વાઇફાઇ ચાલુ કરો'."""
    try:
        from winrt.windows.devices.radios import RadioState
        found, state = _run_coro_sync(_async_set_wifi_state(RadioState.ON))
        if found:
            return "Wi-Fi has been turned on."
        os.system("start ms-settings:network-wifi")
        return "I opened Wi-Fi settings for you to enable Wi-Fi."
    except Exception as e:
        try:
            os.system("start ms-settings:network-wifi")
            return "Opened Wi-Fi settings."
        except Exception:
            return f"Could not turn on Wi-Fi: {e}"


def turn_off_wifi() -> str:
    """Turns off the laptop's Wi-Fi adapter. Use when the user says 'turn off wifi', 'disable wifi', or 'વાઇફાઇ બંધ કરો'."""
    try:
        from winrt.windows.devices.radios import RadioState
        found, state = _run_coro_sync(_async_set_wifi_state(RadioState.OFF))
        if found:
            return "Wi-Fi has been turned off."
        os.system("start ms-settings:network-wifi")
        return "I opened Wi-Fi settings for you to disable Wi-Fi."
    except Exception as e:
        try:
            os.system("start ms-settings:network-wifi")
            return "Opened Wi-Fi settings."
        except Exception:
            return f"Could not turn off Wi-Fi: {e}"


def toggle_wifi() -> str:
    """Toggles the laptop's Wi-Fi adapter on or off depending on current state."""
    try:
        from winrt.windows.devices.radios import RadioState
        curr = _run_coro_sync(_async_get_wifi_state())
        if curr == RadioState.ON:
            return turn_off_wifi()
        else:
            return turn_on_wifi()
    except Exception as e:
        os.system("start ms-settings:network-wifi")
        return f"Toggled Wi-Fi settings ({e})."


def get_wifi_status() -> str:
    """Checks and returns the current status of the laptop's Wi-Fi adapter and connection."""
    try:
        from winrt.windows.devices.radios import RadioState
        import psutil
        curr = _run_coro_sync(_async_get_wifi_state())
        state_str = "On" if curr == RadioState.ON else ("Off" if curr == RadioState.OFF else "Disabled")
        
        # Check active interfaces
        stats = psutil.net_if_stats()
        wifi_up = any(v.isup for k, v in stats.items() if "wi" in k.lower() or "wlan" in k.lower())
        conn_msg = "and connected to network" if wifi_up else "but not connected"
        return f"Wi-Fi is currently {state_str} {conn_msg}."
    except Exception as e:
        return f"Could not determine Wi-Fi status: {e}"


def list_wifi_networks() -> str:
    """Lists available Wi-Fi networks in range or opens the Wi-Fi flyout."""
    try:
        result = subprocess.run(["netsh", "wlan", "show", "networks"], capture_output=True, text=True, timeout=5)
        lines = [line.split(":", 1)[1].strip() for line in result.stdout.splitlines() if "SSID " in line]
        if lines:
            unique_ssids = list(dict.fromkeys(lines))[:8]
            return "Available Wi-Fi networks: " + ", ".join(unique_ssids)
    except Exception:
        pass
    # Quick fallback: launch Windows network flyout / settings
    try:
        import pyautogui
        pyautogui.hotkey('win', 'a')
        return "Opened Quick Settings flyout showing available networks."
    except Exception:
        os.system("start ms-settings:network-wifi")
        return "Opened Wi-Fi settings to view available networks."


def _open_wifi_settings() -> str:
    """Opens Windows Wi-Fi Settings directly."""
    try:
        os.system("start ms-settings:network-wifi")
        return "Opened Windows Wi-Fi settings."
    except Exception as e:
        return f"Could not open Wi-Fi settings: {e}"


# =====================================================================
# 3. MOBILE HOTSPOT CONTROL (Windows NetworkOperator Tethering API)
# =====================================================================

async def _async_set_hotspot(enable: bool):
    from winrt.windows.networking.connectivity import NetworkInformation
    from winrt.windows.networking.networkoperators import (
        NetworkOperatorTetheringManager,
        TetheringOperationalState,
        TetheringOperationStatus,
    )
    profile = NetworkInformation.get_internet_connection_profile()
    if not profile:
        return False, "No active internet connection to share for Mobile Hotspot."
    manager = NetworkOperatorTetheringManager.create_from_connection_profile(profile)
    curr = manager.tethering_operational_state
    if enable:
        if curr == TetheringOperationalState.ON:
            return True, "Mobile Hotspot is already turned On."
        res = await manager.start_tethering_async()
        if res.status == TetheringOperationStatus.SUCCESS:
            return True, "Mobile Hotspot has been turned on."
        return False, f"Could not start Hotspot ({res.status})."
    else:
        if curr == TetheringOperationalState.OFF:
            return True, "Mobile Hotspot is already turned Off."
        res = await manager.stop_tethering_async()
        if res.status == TetheringOperationStatus.SUCCESS:
            return True, "Mobile Hotspot has been turned off."
        return False, f"Could not stop Hotspot ({res.status})."


async def _async_get_hotspot_state():
    from winrt.windows.networking.connectivity import NetworkInformation
    from winrt.windows.networking.networkoperators import (
        NetworkOperatorTetheringManager,
        TetheringOperationalState,
    )
    profile = NetworkInformation.get_internet_connection_profile()
    if not profile:
        return None, 0
    manager = NetworkOperatorTetheringManager.create_from_connection_profile(profile)
    curr = manager.tethering_operational_state
    clients = manager.get_tethering_clients()
    is_on = (curr == TetheringOperationalState.ON)
    return is_on, len(clients) if clients else 0


def turn_on_hotspot() -> str:
    """Turns on the laptop's Mobile Hotspot to share internet connection. Use when the user says 'turn on hotspot', 'enable hotspot', 'start hotspot', or 'હોટસ્પોટ ચાલુ કરો'."""
    try:
        ok, msg = _run_coro_sync(_async_set_hotspot(True))
        if ok:
            return msg
        os.system("start ms-settings:network-mobilehotspot")
        return f"{msg} I opened Mobile Hotspot settings for you."
    except Exception as e:
        os.system("start ms-settings:network-mobilehotspot")
        return "Opened Mobile Hotspot settings to enable hotspot."


def turn_off_hotspot() -> str:
    """Turns off the laptop's Mobile Hotspot. Use when the user says 'turn off hotspot', 'disable hotspot', 'stop hotspot', or 'હોટસ્પોટ બંધ કરો'."""
    try:
        ok, msg = _run_coro_sync(_async_set_hotspot(False))
        if ok:
            return msg
        os.system("start ms-settings:network-mobilehotspot")
        return f"{msg} I opened Mobile Hotspot settings."
    except Exception as e:
        os.system("start ms-settings:network-mobilehotspot")
        return "Opened Mobile Hotspot settings to disable hotspot."


def toggle_hotspot() -> str:
    """Toggles Mobile Hotspot on or off based on current state."""
    try:
        is_on, _ = _run_coro_sync(_async_get_hotspot_state())
        if is_on:
            return turn_off_hotspot()
        else:
            return turn_on_hotspot()
    except Exception:
        os.system("start ms-settings:network-mobilehotspot")
        return "Opened Mobile Hotspot settings."


def get_hotspot_status() -> str:
    """Checks if the laptop's Mobile Hotspot is active and how many devices are connected."""
    try:
        is_on, count = _run_coro_sync(_async_get_hotspot_state())
        if is_on is None:
            return "Mobile Hotspot is currently inactive (no active connection to share)."
        state_str = "On" if is_on else "Off"
        return f"Mobile Hotspot is currently {state_str} with {count} connected device(s)."
    except Exception as e:
        return f"Could not check Hotspot status: {e}"


def _open_hotspot_settings() -> str:
    """Opens Windows Mobile Hotspot Settings directly."""
    try:
        os.system("start ms-settings:network-mobilehotspot")
        return "Opened Mobile Hotspot settings."
    except Exception as e:
        return f"Could not open Mobile Hotspot settings: {e}"


# =====================================================================
# 4. AIRPLANE MODE & QUICK SETTINGS
# =====================================================================

def turn_on_airplane_mode() -> str:
    """Turns on Airplane Mode or opens Airplane Mode settings. Use when user says 'turn on airplane mode' or 'flight mode'."""
    try:
        from winrt.windows.devices.radios import RadioState
        _run_coro_sync(_async_set_wifi_state(RadioState.OFF))
        _run_coro_sync(_async_set_bluetooth_state(RadioState.OFF))
        os.system("start ms-settings:network-airplanemode")
        return "Airplane Mode engaged: Wi-Fi and Bluetooth radios disabled."
    except Exception as e:
        os.system("start ms-settings:network-airplanemode")
        return "Opened Airplane Mode settings."


def turn_off_airplane_mode() -> str:
    """Turns off Airplane Mode and restores laptop radios."""
    try:
        from winrt.windows.devices.radios import RadioState
        _run_coro_sync(_async_set_wifi_state(RadioState.ON))
        _run_coro_sync(_async_set_bluetooth_state(RadioState.ON))
        os.system("start ms-settings:network-airplanemode")
        return "Airplane Mode disabled: Wi-Fi and Bluetooth radios re-enabled."
    except Exception as e:
        os.system("start ms-settings:network-airplanemode")
        return "Opened Airplane Mode settings to turn it off."


def toggle_airplane_mode() -> str:
    """Toggles Airplane Mode."""
    os.system("start ms-settings:network-airplanemode")
    return "Opened Airplane Mode settings to toggle state."


def _open_airplane_mode_settings() -> str:
    """Opens Windows Airplane Mode settings directly."""
    os.system("start ms-settings:network-airplanemode")
    return "Opened Airplane Mode settings."


def open_quick_settings() -> str:
    """Opens the Windows 11/10 Quick Settings / Action Center flyout (Win + A) with quick toggles for Bluetooth, Wi-Fi, Hotspot, Sound, and Brightness."""
    try:
        import pyautogui
        pyautogui.hotkey('win', 'a')
        return "Opened Windows Quick Settings flyout."
    except Exception as e:
        return f"Could not open Quick Settings: {e}"


# =====================================================================
# 5. GENERAL WINDOWS SETTINGS & DISPLAY / AUDIO / BATTERY
# =====================================================================

def open_system_settings(page: str = "") -> str:
    """Opens any Windows Settings page. Examples: 'bluetooth', 'wifi', 'hotspot', 'sound', 'display', 'battery', 'apps', 'updates', 'night light'."""
    page_clean = (page or "").lower().strip()
    routes = {
        "bluetooth": "ms-settings:bluetooth",
        "wifi": "ms-settings:network-wifi",
        "wi-fi": "ms-settings:network-wifi",
        "hotspot": "ms-settings:network-mobilehotspot",
        "mobile hotspot": "ms-settings:network-mobilehotspot",
        "airplane": "ms-settings:network-airplanemode",
        "sound": "ms-settings:sound",
        "audio": "ms-settings:sound",
        "volume": "ms-settings:sound",
        "display": "ms-settings:display",
        "screen": "ms-settings:display",
        "brightness": "ms-settings:display",
        "night light": "ms-settings:nightlight",
        "nightlight": "ms-settings:nightlight",
        "battery": "ms-settings:batterysaver",
        "power": "ms-settings:powersleep",
        "sleep": "ms-settings:powersleep",
        "updates": "ms-settings:windowsupdate",
        "update": "ms-settings:windowsupdate",
        "apps": "ms-settings:appsfeatures",
        "storage": "ms-settings:storagesense",
        "notifications": "ms-settings:notifications",
        "privacy": "ms-settings:privacy",
        "personalization": "ms-settings:personalization",
    }
    target_uri = "ms-settings:"
    for key, uri in routes.items():
        if key in page_clean:
            target_uri = uri
            break

    try:
        os.system(f"start {target_uri}")
        return f"Opened Windows Settings ({page_clean or 'Home'})."
    except Exception as e:
        return f"Could not open Settings: {e}"


def turn_on_night_light() -> str:
    """Opens Night Light settings to enable warm screen colors for eye comfort."""
    os.system("start ms-settings:nightlight")
    return "Opened Windows Night Light settings."


def turn_off_night_light() -> str:
    """Opens Night Light settings to disable night light."""
    os.system("start ms-settings:nightlight")
    return "Opened Windows Night Light settings."


def _open_sound_settings() -> str:
    """Opens Windows Sound settings and Volume Mixer."""
    os.system("start ms-settings:sound")
    return "Opened Windows Sound settings."


def _open_battery_settings() -> str:
    """Opens Windows Battery & Power settings."""
    os.system("start ms-settings:batterysaver")
    return "Opened Windows Battery settings."


# =====================================================================
# 6. TIME, HARDWARE METRICS, REMINDERS & CLIPBOARD
# =====================================================================

def _tell_time() -> str:
    """Returns the current local time."""
    now = datetime.now().strftime("%I:%M %p")
    return f"It is currently {now}."


def _tell_date() -> str:
    """Returns today's full date including the day of the week."""
    today = datetime.now().strftime("%A, %B %d, %Y")
    return f"Today is {today}."


def get_system_info() -> str:
    """Returns detailed real-time system information: CPU usage, RAM, disk space, and battery status."""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        _disk_path = 'C:\\' if os.name == 'nt' else '/'
        disk = psutil.disk_usage(_disk_path)
        battery = psutil.sensors_battery()

        ram_used_gb = ram.used / (1024 ** 3)
        ram_total_gb = ram.total / (1024 ** 3)
        disk_used_gb = disk.used / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)

        info = (
            f"System status: CPU is at {cpu}%. "
            f"RAM usage is {ram.percent}% ({ram_used_gb:.1f} GB used of {ram_total_gb:.1f} GB total). "
            f"Disk usage is {disk.percent}% ({disk_used_gb:.1f} GB used of {disk_total_gb:.1f} GB total)."
        )
        if battery:
            plug_status = "charging" if battery.power_plugged else "on battery"
            info += f" Battery is at {battery.percent:.0f}% and {plug_status}."
        return info
    except Exception as e:
        return f"Could not retrieve system information: {e}"


def check_battery() -> str:
    """Checks the current battery percentage and whether the laptop is plugged in."""
    try:
        import psutil
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            plugged = "and currently charging" if battery.power_plugged else "and running on battery power"
            mins = battery.secsleft // 60 if battery.secsleft > 0 and not battery.power_plugged else None
            msg = f"The battery is at {percent:.0f}% {plugged}."
            if mins:
                msg += f" Approximately {mins} minutes remaining."
            return msg
        return "I couldn't detect a battery. This might be a desktop computer."
    except Exception as e:
        return f"Battery check error: {e}"


def set_reminder(message: str, seconds: str) -> str:
    """Sets a voice reminder that fires after the specified number of seconds. Example: message='drink water', seconds='30'."""
    import threading
    try:
        delay = int(''.join(filter(str.isdigit, seconds)) or '30')
        delay = max(5, min(3600, delay))  # clamp between 5s and 1 hour

        def _fire():
            time.sleep(delay)
            print(f"🔔 REMINDER: {message}")
            try:
                import win32com.client
                import pythoncom
                pythoncom.CoInitialize()
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Speak(f"Reminder: {message}")
            except Exception:
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.say(f"Reminder: {message}")
                    engine.runAndWait()
                except Exception:
                    pass

        threading.Thread(target=_fire, daemon=True).start()
        if delay < 60:
            time_str = f"{delay} seconds"
        else:
            time_str = f"{delay // 60} minute{'s' if delay // 60 > 1 else ''}"
        return f"Reminder set! I will remind you about '{message}' in {time_str}."
    except Exception as e:
        return f"Could not set reminder: {e}"


def get_clipboard() -> str:
    """Reads and returns the current text content from the Windows clipboard."""
    try:
        import pyperclip
        content = pyperclip.paste()
        if not content or not content.strip():
            return "The clipboard is currently empty."
        if len(content) > 500:
            return f"Clipboard content (first 500 chars): {content[:500]}..."
        return f"Clipboard contains: {content}"
    except Exception as e:
        return f"Could not read clipboard: {e}"


def set_clipboard(text: str) -> str:
    """Copies the given text to the Windows clipboard so you can paste it anywhere."""
    try:
        import pyperclip
        pyperclip.copy(text)
        preview = text[:50] + "..." if len(text) > 50 else text
        return f"Copied to clipboard: '{preview}'"
    except Exception as e:
        return f"Could not write to clipboard: {e}"
