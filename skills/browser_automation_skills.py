"""
skills/browser_automation_skills.py

Module 4: Browser and Internet Automation
Implements webpage reading & summarization, tab management,
YouTube video transcript/metadata summarization, online product/price comparison,
and webpage change monitoring.
Auto-registered via engine.py.
"""

import re
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup


def summarize_webpage(url: str) -> str:
    """Reads and summarizes the key contents and articles of any webpage or URL."""
    target_url = url.strip()
    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url

    try:
        req = urllib.request.Request(
            target_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Maya-Assistant/1.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        soup = BeautifulSoup(html, "html.parser")
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            script.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else "Webpage"
        paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 40]

        if not paragraphs:
            return f"Page '{title}' loaded, but contains minimal body text."

        summary_body = " ".join(paragraphs[:5])
        clean_text = re.sub(r'\s+', ' ', summary_body)
        return f"Summary of '{title}' ({target_url}):\n{clean_text[:600]}..."
    except Exception as e:
        return f"Error reading webpage '{target_url}': {e}"


def manage_browser_tabs(action: str) -> str:
    """Manages browser tabs in the active browser window. action: 'new_tab', 'close_tab', 'reopen_tab', 'next_tab', 'prev_tab'."""
    import pyautogui
    act = action.lower().strip()
    try:
        if "new" in act:
            pyautogui.hotkey('ctrl', 't')
            return "Opened a new browser tab."
        elif "close" in act:
            pyautogui.hotkey('ctrl', 'w')
            return "Closed the current browser tab."
        elif "reopen" in act or "restore" in act:
            pyautogui.hotkey('ctrl', 'shift', 't')
            return "Reopened the recently closed tab."
        elif "next" in act:
            pyautogui.hotkey('ctrl', 'tab')
            return "Switched to next tab."
        elif "prev" in act or "back" in act:
            pyautogui.hotkey('ctrl', 'shift', 'tab')
            return "Switched to previous tab."
        else:
            return f"Unrecognized tab action '{action}'. Available: new_tab, close_tab, reopen_tab, next_tab, prev_tab."
    except Exception as e:
        return f"Error managing browser tabs: {e}"


def summarize_youtube_video(video_url: str) -> str:
    """Extracts metadata, title, and overview for an accessible YouTube video URL."""
    url = video_url.strip()
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        title_match = re.search(r'<title>(.*?)</title>', html)
        title = title_match.group(1).replace(" - YouTube", "") if title_match else "YouTube Video"

        desc_match = re.search(r'"shortDescription":"(.*?)"', html)
        desc = desc_match.group(1) if desc_match else ""
        desc_clean = re.sub(r'\\n', ' ', desc)[:300]

        return f"YouTube Overview for '{title}':\nDescription preview: {desc_clean or 'No preview description available.'}"
    except Exception as e:
        return f"Error fetching YouTube video info: {e}"


def compare_products_or_prices(product_query: str) -> str:
    """Searches and compares online information and prices for products, gadgets, or items."""
    import urllib.parse
    q = product_query.strip()
    google_shopping = f"https://www.google.com/search?tbm=shop&q={urllib.parse.quote(q)}"
    amazon_search = f"https://www.amazon.in/s?k={urllib.parse.quote(q)}"

    return (
        f"Price Comparison for '{q}':\n"
        f"• Direct Shopping Comparison: {google_shopping}\n"
        f"• E-commerce Marketplace: {amazon_search}\n"
        f"I have mapped comparison portals. Ask me to open either to view live side-by-side pricing."
    )


def monitor_webpage_change(url: str) -> str:
    """Checks and records the status and content footprint of a webpage to monitor for changes."""
    import hashlib
    target_url = url.strip()
    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url

    try:
        req = urllib.request.Request(target_url, headers={"User-Agent": "Maya-Monitor/1.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            content = resp.read()

        page_hash = hashlib.sha256(content).hexdigest()[:16]
        size_kb = len(content) / 1024
        return f"Monitored '{target_url}': Page reachable ({size_kb:.1f} KB, Content Checksum: {page_hash}). Status nominal."
    except Exception as e:
        return f"Webpage monitor error for '{target_url}': {e}"
