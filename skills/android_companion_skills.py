"""
skills/android_companion_skills.py

Module 13: Android Companion
Implements Android phone integration via ADB or network companion:
device status, SMS composition, remote app launching, and PC-to-phone file transfer.
Auto-registered via engine.py.
"""

import subprocess
import shutil
import os


def _check_adb() -> bool:
    return shutil.which("adb") is not None


def android_device_status() -> str:
    """Checks the connection status and battery of a connected Android smartphone."""
    if not _check_adb():
        return "Android Companion Status: Simulated Mode. (Connect phone via USB/Wi-Fi and install Android Platform Tools for live ADB pairing)."

    try:
        res = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
        lines = [l for l in res.stdout.splitlines() if "\tdevice" in l]
        if not lines:
            return "Android Companion: No Android device detected. Please enable USB Debugging on your phone."

        device_id = lines[0].split("\t")[0]
        # Query battery
        bat_res = subprocess.run(["adb", "-s", device_id, "shell", "dumpsys", "battery"], capture_output=True, text=True, timeout=5)
        level = "N/A"
        for line in bat_res.stdout.splitlines():
            if "level:" in line:
                level = line.split(":")[-1].strip() + "%"
                break
        return f"Connected Android Device: ID {device_id}, Battery {level}. Ready for commands."
    except Exception as e:
        return f"Error checking Android device: {e}"


def android_send_sms(phone_number: str, message: str) -> str:
    """Composes or sends an SMS message on the connected Android smartphone."""
    if not _check_adb():
        return f"[Android Companion Simulated]: SMS drafted for {phone_number}: '{message}'."

    try:
        # Launch Android SMS intent
        subprocess.run([
            "adb", "shell", "am", "start", "-a", "android.intent.action.SENDTO",
            "-d", f"sms:{phone_number}", "--es", "sms_body", message, "--ez", "exit_on_sent", "true"
        ], capture_output=True, timeout=5)
        return f"Android Companion: SMS compose screen opened on phone for {phone_number}."
    except Exception as e:
        return f"Error sending SMS via Android companion: {e}"


def android_open_app(app_name: str) -> str:
    """Launches an application on the connected Android smartphone."""
    app_lower = app_name.lower().strip()
    packages = {
        "whatsapp": "com.whatsapp",
        "youtube": "com.google.android.youtube",
        "maps": "com.google.android.apps.maps",
        "spotify": "com.spotify.music",
        "camera": "com.android.camera",
        "settings": "com.android.settings",
    }
    pkg = packages.get(app_lower, f"com.{app_lower}")

    if not _check_adb():
        return f"[Android Companion Simulated]: Launched app '{app_name}' (package {pkg}) on phone."

    try:
        subprocess.run(["adb", "shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True, timeout=5)
        return f"Android Companion: Launched '{app_name}' on phone."
    except Exception as e:
        return f"Error launching app on phone: {e}"


def android_push_file(file_path: str, destination_folder: str = "/sdcard/Download") -> str:
    """Transfers a file from PC to the connected Android phone's Download folder."""
    if not os.path.exists(file_path):
        return f"Local file not found: '{file_path}'."

    if not _check_adb():
        return f"[Android Companion Simulated]: Transferred '{os.path.basename(file_path)}' to Android {destination_folder}."

    try:
        subprocess.run(["adb", "push", file_path, destination_folder], capture_output=True, timeout=15)
        return f"Android Companion: Pushed '{os.path.basename(file_path)}' to {destination_folder} on your phone."
    except Exception as e:
        return f"Error pushing file to phone: {e}"
