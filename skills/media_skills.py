"""
skills/media_skills.py

Media and music control — play/pause/skip, volume, Spotify, YouTube Music.
Auto-registered as Groq tools via engine.py.
"""
import time


def pause_resume_media() -> str:
    """Pauses or resumes the currently playing media (music, video, podcast) using the system media key."""
    try:
        import pyautogui
        pyautogui.press('playpause')
        return "Media play/pause toggled."
    except Exception as e:
        return f"Could not toggle media: {e}"


def next_track() -> str:
    """Skips to the next track or chapter in any media player (Spotify, VLC, Windows Media Player, YouTube Music, etc.)."""
    try:
        import pyautogui
        pyautogui.press('nexttrack')
        return "Skipped to next track."
    except Exception as e:
        return f"Could not skip track: {e}"


def previous_track() -> str:
    """Goes back to the previous track in any media player."""
    try:
        import pyautogui
        pyautogui.press('prevtrack')
        return "Went back to previous track."
    except Exception as e:
        return f"Could not go to previous track: {e}"


def mute_unmute_media() -> str:
    """Mutes or unmutes the system audio/speakers."""
    try:
        import pyautogui
        pyautogui.press('volumemute')
        return "Audio muted or unmuted."
    except Exception as e:
        return f"Could not mute/unmute: {e}"


def _resolve_and_play_youtube(query: str) -> str:
    """Internal helper to resolve the exact YouTube video watch URL and launch it in Chrome/browser."""
    import urllib.request, urllib.parse, re, os, subprocess, webbrowser
    clean_query = query.strip()
    encoded = urllib.parse.quote_plus(clean_query)
    search_url = f"https://www.youtube.com/results?search_query={encoded}"
    watch_url = None

    # 1. Direct fast HTML scrape (extract first video id)
    try:
        req = urllib.request.Request(
            search_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            video_ids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
            if video_ids:
                watch_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
    except Exception:
        pass

    # 2. PyWhatKit fallback
    if not watch_url:
        try:
            import pywhatkit
            resolved = pywhatkit.playonyt(clean_query, open_video=False)
            if resolved and "watch?v=" in resolved:
                watch_url = resolved
        except Exception:
            pass

    target_url = watch_url or search_url

    # 3. Launch directly in Google Chrome if installed, or fallback to default browser
    candidates = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    launched = False
    for chrome_path in candidates:
        if os.path.exists(chrome_path):
            try:
                subprocess.Popen([chrome_path, target_url])
                launched = True
                break
            except Exception:
                pass

    if not launched:
        try:
            subprocess.Popen(["cmd.exe", "/c", "start", "chrome", target_url], shell=True)
            launched = True
        except Exception:
            pass

    if not launched:
        webbrowser.open(target_url)

    if watch_url:
        return f"Now playing '{clean_query}' on YouTube in Chrome."
    return f"Opened YouTube search for '{clean_query}'."


def play_on_youtube(query: str) -> str:
    """Finds and immediately plays any video, song, music, trailer, or clip on YouTube in Google Chrome or default browser. Use this whenever the user asks to play a song/video, or says compound commands like 'open chrome search youtube and play X' or 'find X on youtube and play it'."""
    return _resolve_and_play_youtube(query)


def play_music_youtube(query: str) -> str:
    """Searches and immediately plays music or songs on YouTube in Google Chrome or default browser. Example: query='Bollywood songs', 'Ishq De Fanniyar', 'Arijit Singh', 'lo-fi beats'."""
    return _resolve_and_play_youtube(query)



def play_spotify(query: str) -> str:
    """Opens Spotify and searches for a song, artist, album, or playlist. Example: query='Taylor Swift', 'chill beats'."""
    import webbrowser, urllib.parse
    encoded = urllib.parse.quote(query)
    webbrowser.open(f"https://open.spotify.com/search/{encoded}")
    return f"Opening Spotify search for '{query}'."


def set_volume_percent(percent: str) -> str:
    """Sets the Windows system volume to a specific percentage. Example: percent='50' for 50% volume, '100' for max."""
    try:
        import pyautogui, subprocess
        level = max(0, min(100, int(''.join(filter(str.isdigit, percent)) or '50')))
        # Use PowerShell to set exact volume level
        script = f"""
$obj = New-Object -ComObject WScript.Shell
for ($i=0; $i -le 50; $i++) {{ $obj.SendKeys([char]174) }}
$steps = [Math]::Round({level} / 2)
for ($i=0; $i -lt $steps; $i++) {{ $obj.SendKeys([char]175) }}
"""
        subprocess.run(["powershell", "-Command", script],
                       capture_output=True, timeout=5)
        return f"System volume set to approximately {level}%."
    except Exception as e:
        return f"Could not set volume: {e}"


def open_media_player() -> str:
    """Opens the Windows default media player (Windows Media Player or Movies & TV)."""
    import subprocess
    try:
        subprocess.Popen(["start", "wmplayer"], shell=True)
        return "Opening Windows Media Player."
    except Exception:
        try:
            subprocess.Popen(["explorer.exe", "shell:AppsFolder\\Microsoft.ZuneVideo_8wekyb3d8bbwe!Microsoft.ZuneVideo"])
            return "Opening Movies & TV."
        except Exception as e:
            return f"Could not open media player: {e}"


def play_radio_station(genre: str) -> str:
    """Plays an online radio station based on genre (e.g. 'jazz', 'pop', 'classical', 'rock', 'hip hop', 'lofi') via a browser stream."""
    import webbrowser
    stations = {
        "jazz":        "https://www.radiooooo.com/",
        "lofi":        "https://www.youtube.com/watch?v=jfKfPfyJRdk",
        "classical":   "https://www.youtube.com/watch?v=SHs5MSE8RIc",
        "pop":         "https://www.youtube.com/watch?v=K4TOrB7at0Y",
        "rock":        "https://www.youtube.com/watch?v=EBwEk18CQZE",
        "hip hop":     "https://www.youtube.com/watch?v=hHW1oY26kxQ",
        "chill":       "https://www.youtube.com/watch?v=jfKfPfyJRdk",
        "study":       "https://www.youtube.com/watch?v=jfKfPfyJRdk",
        "bollywood":   "https://music.youtube.com/search?q=bollywood+hits",
        "devotional":  "https://music.youtube.com/search?q=devotional+songs",
    }
    g = genre.lower().strip()
    url = None
    for key, val in stations.items():
        if key in g:
            url = val
            break
    if not url:
        url = f"https://music.youtube.com/search?q={genre.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Playing {genre} radio/music in your browser."
