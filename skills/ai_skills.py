"""
skills/ai_skills.py

Advanced AI-powered utility tools — compression, QR codes, text analysis,
file operations, and internet connectivity checks.
Auto-registered as Groq tools via engine.py.
"""
import os
import subprocess


def compress_folder(folder_path: str, output_name: str) -> str:
    """Compresses/zips a folder into a .zip file. folder_path is the folder to compress, output_name is the zip filename (without .zip)."""
    import zipfile, os
    try:
        if not os.path.exists(folder_path):
            return f"Folder not found: '{folder_path}'."
        output_zip = output_name.rstrip(".zip") + ".zip"
        if not os.path.isabs(output_zip):
            output_zip = os.path.join(os.path.dirname(folder_path), output_zip)
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname   = os.path.relpath(file_path, os.path.dirname(folder_path))
                    zf.write(file_path, arcname)
        size_mb = os.path.getsize(output_zip) / (1024 * 1024)
        return f"Compressed to '{os.path.basename(output_zip)}' ({size_mb:.2f} MB)."
    except Exception as e:
        return f"Compression failed: {e}"


def extract_zip(zip_path: str, output_folder: str) -> str:
    """Extracts/unzips a .zip file to the specified output folder. If output_folder is empty, extracts next to the zip file."""
    import zipfile
    try:
        if not os.path.exists(zip_path):
            return f"Zip file not found: '{zip_path}'."
        if not output_folder.strip():
            output_folder = os.path.splitext(zip_path)[0]
        os.makedirs(output_folder, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(output_folder)
            count = len(zf.namelist())
        return f"Extracted {count} file(s) to '{output_folder}'."
    except Exception as e:
        return f"Extraction failed: {e}"


def generate_qr_code(text: str) -> str:
    """Generates a QR code image for any text, URL, or message and saves it to the Desktop."""
    try:
        import qrcode
        from PIL import Image
        desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
        os.makedirs(desktop, exist_ok=True)
        filename = "maya_qrcode.png"
        filepath = os.path.join(desktop, filename)
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(filepath)
        os.startfile(filepath)
        return f"QR code generated and saved to Desktop as '{filename}'."
    except ImportError:
        return "QR code generation requires 'qrcode' and 'Pillow'. Run: pip install qrcode pillow"
    except Exception as e:
        return f"QR code generation failed: {e}"


def check_internet_speed() -> str:
    """Checks the current internet download and upload speed using an online speed test."""
    try:
        import speedtest
        st = speedtest.Speedtest(secure=True)
        st.get_best_server()
        download = st.download() / 1_000_000
        upload   = st.upload()   / 1_000_000
        ping_ms  = st.results.ping
        return (f"Internet speed: Download {download:.1f} Mbps, "
                f"Upload {upload:.1f} Mbps, Ping {ping_ms:.0f} ms.")
    except ImportError:
        return "Speed test requires 'speedtest-cli'. Run: pip install speedtest-cli"
    except Exception as e:
        return f"Speed test failed: {e}"


def analyze_sentiment(text: str) -> str:
    """Analyzes the emotional tone/sentiment of a given text and returns whether it is positive, negative, or neutral."""
    try:
        # Simple keyword-based sentiment analysis (no external ML libs needed)
        positive_words = [
            "good", "great", "excellent", "amazing", "wonderful", "fantastic",
            "love", "happy", "best", "awesome", "brilliant", "perfect",
            "beautiful", "superb", "outstanding", "positive", "success",
            "congratulations", "thank", "appreciate", "joy", "pleased",
        ]
        negative_words = [
            "bad", "terrible", "awful", "horrible", "hate", "worst",
            "disgusting", "ugly", "failed", "failure", "angry", "sad",
            "depressed", "useless", "stupid", "wrong", "error", "problem",
            "issue", "broken", "frustrating", "disappointing", "poor",
        ]
        words_lower = text.lower().split()
        pos_count = sum(1 for w in words_lower if any(pw in w for pw in positive_words))
        neg_count = sum(1 for w in words_lower if any(nw in w for nw in negative_words))

        if pos_count > neg_count:
            sentiment = "POSITIVE"
            emoji = "😊"
        elif neg_count > pos_count:
            sentiment = "NEGATIVE"
            emoji = "😞"
        else:
            sentiment = "NEUTRAL"
            emoji = "😐"

        return (f"Sentiment: {sentiment} {emoji}. "
                f"Found {pos_count} positive signal(s) and {neg_count} negative signal(s) in the text.")
    except Exception as e:
        return f"Sentiment analysis error: {e}"


def open_file(file_path: str) -> str:
    """Opens any file using the default Windows application for that file type (e.g., PDF opens in Acrobat, .mp3 opens in Windows Media Player)."""
    try:
        profile  = os.environ.get("USERPROFILE", "")
        shortcuts = {
            "desktop":   os.path.join(profile, "Desktop"),
            "documents": os.path.join(profile, "Documents"),
            "downloads": os.path.join(profile, "Downloads"),
        }
        for key, val in shortcuts.items():
            if file_path.lower().startswith(key):
                file_path = os.path.join(val, file_path[len(key):].lstrip("\\/"))
                break

        if not os.path.exists(file_path):
            # Search Desktop and Documents
            for search_dir in [os.path.join(profile, "Desktop"),
                               os.path.join(profile, "Documents")]:
                for root, dirs, files in os.walk(search_dir):
                    for f in files:
                        if os.path.basename(file_path).lower() in f.lower():
                            file_path = os.path.join(root, f)
                            break
                    else:
                        continue
                    break

        if os.path.exists(file_path):
            os.startfile(file_path)
            return f"Opened: '{os.path.basename(file_path)}'."
        return f"File not found: '{file_path}'."
    except Exception as e:
        return f"Could not open file: {e}"


def find_files(filename: str, search_location: str) -> str:
    """Searches for files by name within a folder. search_location can be 'Desktop', 'Documents', 'Downloads', or a full path."""
    import fnmatch
    try:
        profile  = os.environ.get("USERPROFILE", "")
        shortcuts = {
            "desktop":   os.path.join(profile, "Desktop"),
            "documents": os.path.join(profile, "Documents"),
            "downloads": os.path.join(profile, "Downloads"),
            "c":         "C:\\",
        }
        loc = shortcuts.get(search_location.lower().strip(),
                            search_location if os.path.isdir(search_location)
                            else os.path.join(profile, "Desktop"))

        matches = []
        for root, dirs, files in os.walk(loc):
            # Skip hidden/system dirs
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                       ['$Recycle.Bin', 'System Volume Information', 'Windows', 'Program Files']]
            for f in files:
                if fnmatch.fnmatch(f.lower(), f"*{filename.lower()}*"):
                    matches.append(os.path.join(root, f))
            if len(matches) >= 10:
                break

        if matches:
            return (f"Found {len(matches)} file(s) matching '{filename}': "
                    + "; ".join(os.path.basename(m) + f" ({os.path.dirname(m)})"
                                for m in matches[:5])
                    + ("..." if len(matches) > 5 else ""))
        return f"No files found matching '{filename}' in {loc}."
    except Exception as e:
        return f"File search error: {e}"


def read_csv_file(file_path: str) -> str:
    """Reads a CSV file and returns a summary of its contents including column names, row count, and first few rows."""
    try:
        import csv
        profile = os.environ.get("USERPROFILE", "")
        shortcuts = {
            "desktop":   os.path.join(profile, "Desktop"),
            "documents": os.path.join(profile, "Documents"),
            "downloads": os.path.join(profile, "Downloads"),
        }
        for key, val in shortcuts.items():
            if file_path.lower().startswith(key):
                file_path = os.path.join(val, file_path[len(key):].lstrip("\\/"))
                break

        if not os.path.exists(file_path):
            return f"CSV file not found: '{file_path}'."

        with open(file_path, encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            rows   = list(reader)

        if not rows:
            return "The CSV file is empty."

        headers = rows[0]
        data_rows = rows[1:]
        preview = "; ".join(str(row) for row in data_rows[:3])

        return (f"CSV file '{os.path.basename(file_path)}': "
                f"{len(headers)} columns ({', '.join(headers[:6])}{'...' if len(headers)>6 else ''}), "
                f"{len(data_rows)} data rows. "
                f"First rows: {preview[:300]}")
    except Exception as e:
        return f"Could not read CSV: {e}"


def get_system_info() -> str:
    """Returns comprehensive system information — OS version, processor, RAM, Python version, computer name, and uptime."""
    import platform, psutil, datetime as dt
    try:
        uname    = platform.uname()
        boot     = psutil.boot_time()
        boot_dt  = dt.datetime.fromtimestamp(boot)
        uptime   = dt.datetime.now() - boot_dt
        h, rem   = divmod(int(uptime.total_seconds()), 3600)
        m, s     = divmod(rem, 60)

        mem_total = psutil.virtual_memory().total / (1024**3)

        return (f"System: {uname.system} {uname.release} ({uname.version[:30]}...). "
                f"Computer name: {uname.node}. "
                f"Processor: {uname.processor[:50] if uname.processor else 'Unknown'}. "
                f"RAM: {mem_total:.1f} GB. "
                f"Python {platform.python_version()}. "
                f"Uptime: {h}h {m}m {s}s.")
    except Exception as e:
        return f"Could not get system info: {e}"
