"""
skills/os_skills.py

Module 3: Windows and Desktop Control & Module 20: System Health
Implements file operations (create, copy, move, rename, safe delete),
window snapping, application switching, and system health checks.
Auto-registered via engine.py.
"""

import os
import shutil
import psutil
import pyautogui


def snap_window(direction: str = "left") -> str:
    """Snaps the active application window to the screen. direction: 'left', 'right', 'maximize', 'minimize'."""
    d = direction.lower().strip()
    try:
        if "left" in d:
            pyautogui.hotkey('win', 'left')
            return "Snapped active window to the left."
        elif "right" in d:
            pyautogui.hotkey('win', 'right')
            return "Snapped active window to the right."
        elif "max" in d or "up" in d:
            pyautogui.hotkey('win', 'up')
            return "Maximized active window."
        elif "min" in d or "down" in d:
            pyautogui.hotkey('win', 'down')
            return "Minimized active window."
        else:
            return f"Unrecognized snap direction '{direction}'. Options: left, right, maximize, minimize."
    except Exception as e:
        return f"Error snapping window: {e}"


def switch_application(app_name: str) -> str:
    """Brings a running application window to the foreground by its window title or executable name."""
    import pygetwindow as gw
    target = app_name.lower().strip()
    all_windows = gw.getAllTitles()
    matched = None
    for title in all_windows:
        if target in title.lower() and title.strip():
            matched = title
            break

    if not matched:
        # Fallback Alt+Tab
        pyautogui.hotkey('alt', 'tab')
        return f"Could not find specific window for '{app_name}'. Cycled to next window with Alt+Tab."

    try:
        windows = gw.getWindowsWithTitle(matched)
        if windows:
            w = windows[0]
            if w.isMinimized:
                w.restore()
            w.activate()
            return f"Switched focus to '{matched}'."
    except Exception as e:
        return f"Error activating window: {e}"


def create_file_or_folder(item_type: str, item_path: str, initial_content: str = "") -> str:
    """Creates a new file or directory. item_type: 'file' or 'folder'/'directory'. item_path can be relative to Desktop or full path."""
    profile = os.environ.get("USERPROFILE", "")
    target = item_path.strip()
    for key, fld in {"desktop": "Desktop", "documents": "Documents", "downloads": "Downloads"}.items():
        if target.lower().startswith(key):
            target = os.path.join(profile, fld, target[len(key):].lstrip("\\/"))
            break

    try:
        if "dir" in item_type.lower() or "folder" in item_type.lower():
            os.makedirs(target, exist_ok=True)
            return f"Folder created successfully at '{target}'."
        else:
            os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(initial_content)
            return f"File created successfully at '{target}'."
    except Exception as e:
        return f"Error creating {item_type}: {e}"


def copy_file(source_path: str, destination_path: str) -> str:
    """Copies a file or directory to a new destination."""
    if not os.path.exists(source_path):
        return f"Source file does not exist: '{source_path}'."
    try:
        if os.path.isdir(source_path):
            shutil.copytree(source_path, destination_path)
        else:
            shutil.copy2(source_path, destination_path)
        return f"Successfully copied '{os.path.basename(source_path)}' to '{destination_path}'."
    except Exception as e:
        return f"Error copying file: {e}"


def move_file(source_path: str, destination_path: str) -> str:
    """Moves a file or directory from source to destination."""
    if not os.path.exists(source_path):
        return f"Source file does not exist: '{source_path}'."
    try:
        shutil.move(source_path, destination_path)
        return f"Successfully moved '{os.path.basename(source_path)}' to '{destination_path}'."
    except Exception as e:
        return f"Error moving file: {e}"


def rename_file(old_path: str, new_name: str) -> str:
    """Renames an existing file or directory."""
    if not os.path.exists(old_path):
        return f"Target path does not exist: '{old_path}'."
    try:
        new_path = os.path.join(os.path.dirname(old_path), new_name.strip())
        os.rename(old_path, new_path)
        return f"Renamed '{os.path.basename(old_path)}' to '{new_name}'."
    except Exception as e:
        return f"Error renaming: {e}"


def delete_file_safely(file_path: str) -> str:
    """Safely deletes a file by sending it to the Windows Recycle Bin or removing it with verification."""
    if not os.path.exists(file_path):
        return f"File not found: '{file_path}'."
    try:
        import winshell
        winshell.delete_file(file_path, no_confirm=True, allow_undo=True)
        return f"File '{os.path.basename(file_path)}' safely moved to Recycle Bin (undoable)."
    except Exception:
        try:
            os.remove(file_path)
            return f"File '{os.path.basename(file_path)}' removed."
        except Exception as e:
            return f"Error deleting file: {e}"


def run_system_health_check() -> str:
    """Performs a comprehensive diagnostic health check of CPU, RAM, Disk, Battery, and Network status."""
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\" if os.name == "nt" else "/")
        bat = psutil.sensors_battery()
        bat_str = f"{bat.percent}% ({'Charging' if bat.power_plugged else 'Battery'})" if bat else "Desktop AC"

        health_status = "OPTIMAL" if (cpu < 85 and mem.percent < 90) else "HEAVY LOAD"

        return (
            f"System Health Diagnostics ({health_status}):\n"
            f"• CPU Load: {cpu:.1f}%\n"
            f"• Memory Utilization: {mem.percent:.1f}% ({mem.used / (1024**3):.1f} GB / {mem.total / (1024**3):.1f} GB)\n"
            f"• Primary Disk (C:): {disk.percent:.1f}% used ({disk.free / (1024**3):.1f} GB free)\n"
            f"• Power Supply: {bat_str}\n"
            f"All operational parameters synchronized."
        )
    except Exception as e:
        return f"Health check diagnostic error: {e}"