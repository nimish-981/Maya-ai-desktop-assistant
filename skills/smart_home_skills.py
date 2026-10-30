"""
skills/smart_home_skills.py

Advanced PC Control — file management, process control, network,
power management, and desktop customization.
Auto-registered as Groq tools via engine.py.
"""
import os
import subprocess
import time


def get_ip_address() -> str:
    """Returns the local IP address and the public-facing IP address of this computer."""
    import socket, urllib.request
    result = ""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        result += f"Local IP: {local_ip}. "
    except Exception:
        result += "Could not determine local IP. "
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as r:
            public_ip = r.read().decode()
        result += f"Public IP: {public_ip}."
    except Exception:
        result += "Could not fetch public IP (check internet)."
    return result


def ping_host(host: str) -> str:
    """Pings a hostname or IP address (e.g., 'google.com', '8.8.8.8') and reports if it is reachable."""
    try:
        result = subprocess.run(
            ["ping", "-n", "3", host],
            capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.strip().splitlines()
        # Find summary line
        for line in reversed(lines):
            if "Average" in line or "Lost" in line or "ms" in line.lower():
                return f"Ping {host}: {line.strip()}"
        return f"Ping to {host} complete. {'Reachable' if result.returncode == 0 else 'Unreachable'}."
    except Exception as e:
        return f"Ping failed: {e}"


def get_running_processes() -> str:
    """Lists the top 10 processes currently using the most CPU on this computer."""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
            try:
                procs.append(p.info)
            except Exception:
                pass
        # Take a real CPU reading
        time.sleep(0.5)
        for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
            try:
                for stored in procs:
                    if stored['name'] == p.info['name']:
                        stored['cpu_percent'] = p.info['cpu_percent']
            except Exception:
                pass

        top = sorted(procs, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:10]
        lines = [f"{p['name']} (CPU: {p.get('cpu_percent',0):.1f}%, RAM: {p.get('memory_percent',0):.1f}%)"
                 for p in top if p.get('name')]
        return "Top processes: " + "; ".join(lines)
    except Exception as e:
        return f"Could not get processes: {e}"


def kill_process(process_name: str) -> str:
    """Kills/terminates a running process by its name. Example: process_name='chrome' or 'notepad.exe'."""
    try:
        import psutil
        name_lower = process_name.lower().strip()
        if not name_lower.endswith('.exe'):
            name_lower_exe = name_lower + '.exe'
        else:
            name_lower_exe = name_lower

        killed = 0
        for p in psutil.process_iter(['name', 'pid']):
            try:
                pname = (p.info['name'] or '').lower()
                if pname == name_lower or pname == name_lower_exe:
                    p.kill()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if killed > 0:
            return f"Terminated {killed} instance(s) of '{process_name}'."
        # Fallback via taskkill
        subprocess.run(["taskkill", "/f", "/im", name_lower_exe], capture_output=True)
        return f"Attempted to force-kill '{process_name}'."
    except Exception as e:
        return f"Could not kill '{process_name}': {e}"


def create_folder(folder_path: str) -> str:
    """Creates a new folder/directory at the given path. Use common locations like 'Desktop/MyFolder', 'Documents/Projects', or a full path."""
    try:
        profile = os.environ.get("USERPROFILE", "C:\\Users\\User")
        shortcuts = {
            "desktop":   os.path.join(profile, "Desktop"),
            "documents": os.path.join(profile, "Documents"),
            "downloads": os.path.join(profile, "Downloads"),
        }
        for key, val in shortcuts.items():
            if folder_path.lower().startswith(key):
                folder_path = folder_path.replace(folder_path[:len(key)], val, 1)
                break

        os.makedirs(folder_path, exist_ok=True)
        return f"Folder created: '{folder_path}'."
    except Exception as e:
        return f"Could not create folder: {e}"


def delete_file(file_path: str) -> str:
    """Safely deletes a file at the specified path. Ask for confirmation if unsure."""
    try:
        profile = os.environ.get("USERPROFILE", "C:\\Users\\User")
        shortcuts = {"desktop": os.path.join(profile, "Desktop"),
                     "documents": os.path.join(profile, "Documents"),
                     "downloads": os.path.join(profile, "Downloads")}
        for key, val in shortcuts.items():
            if file_path.lower().startswith(key):
                file_path = file_path.replace(file_path[:len(key)], val, 1)
                break

        if not os.path.exists(file_path):
            return f"File not found: '{file_path}'."
        if os.path.isdir(file_path):
            return "That path is a folder, not a file. Use a file path instead."
        os.remove(file_path)
        return f"Deleted: '{os.path.basename(file_path)}'."
    except PermissionError:
        return f"Access denied to delete '{file_path}'."
    except Exception as e:
        return f"Could not delete file: {e}"


def rename_file(old_path: str, new_name: str) -> str:
    """Renames a file or folder. old_path is the full path to the file, new_name is just the new filename."""
    try:
        if not os.path.exists(old_path):
            return f"File not found: '{old_path}'."
        parent = os.path.dirname(old_path)
        new_path = os.path.join(parent, new_name)
        os.rename(old_path, new_path)
        return f"Renamed to '{new_name}'."
    except Exception as e:
        return f"Could not rename: {e}"


def get_disk_info() -> str:
    """Returns storage information for all connected drives (C:, D:, etc.) including used and free space."""
    try:
        import psutil, shutil
        parts = psutil.disk_partitions()
        results = []
        for p in parts:
            try:
                usage = shutil.disk_usage(p.mountpoint)
                total_gb = usage.total / (1024**3)
                used_gb  = usage.used  / (1024**3)
                free_gb  = usage.free  / (1024**3)
                pct      = usage.used / usage.total * 100
                results.append(
                    f"{p.mountpoint}: {used_gb:.1f} GB used / {total_gb:.1f} GB total ({pct:.0f}% full, {free_gb:.1f} GB free)"
                )
            except Exception:
                pass
        return "Disk info: " + "; ".join(results) if results else "No disk info available."
    except Exception as e:
        return f"Disk info error: {e}"


def shutdown_pc(delay_minutes: str) -> str:
    """Schedules a Windows PC shutdown after the given number of minutes. Use '0' for immediate shutdown."""
    try:
        mins = max(0, int(''.join(filter(str.isdigit, delay_minutes)) or '0'))
        secs = mins * 60
        subprocess.run(["shutdown", "/s", "/t", str(secs)], capture_output=True)
        if mins == 0:
            return "Shutting down immediately. Goodbye!"
        return f"PC will shut down in {mins} minute{'s' if mins != 1 else ''}."
    except Exception as e:
        return f"Shutdown command failed: {e}"


def restart_pc(delay_minutes: str) -> str:
    """Restarts the Windows PC after the given number of minutes. Use '0' for immediate restart."""
    try:
        mins = max(0, int(''.join(filter(str.isdigit, delay_minutes)) or '0'))
        secs = mins * 60
        subprocess.run(["shutdown", "/r", "/t", str(secs)], capture_output=True)
        if mins == 0:
            return "Restarting immediately!"
        return f"PC will restart in {mins} minute{'s' if mins != 1 else ''}."
    except Exception as e:
        return f"Restart command failed: {e}"


def cancel_shutdown() -> str:
    """Cancels any scheduled shutdown or restart that was previously set."""
    try:
        subprocess.run(["shutdown", "/a"], capture_output=True)
        return "Scheduled shutdown/restart has been cancelled."
    except Exception as e:
        return f"Could not cancel shutdown: {e}"


def sleep_pc() -> str:
    """Puts the Windows computer into sleep/suspend mode immediately."""
    try:
        subprocess.run(["powercfg", "/hibernate", "off"], capture_output=True)
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
                       capture_output=True)
        return "Putting the PC to sleep now."
    except Exception as e:
        return f"Could not sleep PC: {e}"


def set_wallpaper(image_path: str) -> str:
    """Changes the Windows desktop wallpaper to the image at the given file path. Supports JPG and PNG."""
    try:
        import ctypes
        if not os.path.isabs(image_path):
            # Try Desktop first
            profile = os.environ.get("USERPROFILE", "")
            candidate = os.path.join(profile, "Desktop", image_path)
            if os.path.exists(candidate):
                image_path = candidate
        if not os.path.exists(image_path):
            return f"Image not found: '{image_path}'."
        abs_path = os.path.abspath(image_path)
        ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
        return f"Desktop wallpaper changed to '{os.path.basename(image_path)}'."
    except Exception as e:
        return f"Could not change wallpaper: {e}"


def empty_recycle_bin() -> str:
    """Empties the Windows Recycle Bin, permanently deleting all files inside it."""
    try:
        import ctypes
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
        return "Recycle Bin has been emptied."
    except Exception:
        try:
            import winshell
            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
            return "Recycle Bin has been emptied."
        except Exception as e2:
            return f"Could not empty Recycle Bin: {e2}"
    except Exception as e:
        return f"Could not empty Recycle Bin: {e}"
