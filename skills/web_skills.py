"""
skills/web_skills.py

Web browsing and online information tools.
These functions are auto-registered as Groq tools via engine.py.
"""
import webbrowser
import urllib.parse
import urllib.request
import json


def open_google() -> str:
    """Opens Google in the default web browser."""
    webbrowser.open("https://google.com")
    return "Opening Google."


def search_web(query: str) -> str:
    """Searches Google for the given query and opens the results in the browser."""
    encoded = urllib.parse.quote(query)
    webbrowser.open(f"https://google.com/search?q={encoded}")
    return f"Searching the web for '{query}'."


def search_youtube(query: str) -> str:
    """Searches YouTube and immediately plays the requested video or song in Google Chrome or default browser."""
    from skills.media_skills import _resolve_and_play_youtube
    return _resolve_and_play_youtube(query)



def get_weather(city: str) -> str:
    """Fetches the current weather conditions for any city in the world. No API key needed."""
    try:
        encoded_city = urllib.parse.quote(city)
        url = f"https://wttr.in/{encoded_city}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "Maya-Assistant/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            current = data["current_condition"][0]
            temp_c = current["temp_C"]
            temp_f = current["temp_F"]
            feels_c = current["FeelsLikeC"]
            humidity = current["humidity"]
            desc = current["weatherDesc"][0]["value"]
            wind_kmph = current["windspeedKmph"]
            area = data.get("nearest_area", [{}])[0]
            area_name = area.get("areaName", [{}])[0].get("value", city)
            country = area.get("country", [{}])[0].get("value", "")
            return (
                f"Weather in {area_name}, {country}: {desc}. "
                f"Temperature is {temp_c}°C ({temp_f}°F), feels like {feels_c}°C. "
                f"Humidity is {humidity}% and wind speed is {wind_kmph} km/h."
            )
    except urllib.error.URLError:
        return "I could not fetch weather data. Please check your internet connection."
    except Exception as e:
        return f"Weather service error for '{city}': {e}"


def get_news() -> str:
    """Fetches the top 5 latest news headlines from BBC News RSS feed."""
    try:
        url = "http://feeds.bbci.co.uk/news/rss.xml"
        req = urllib.request.Request(url, headers={"User-Agent": "Maya-Assistant/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read().decode("utf-8", errors="ignore")

        # Simple XML parsing — no external libs needed
        import re
        items = re.findall(r"<item>(.*?)</item>", content, re.DOTALL)
        headlines = []
        for i, item in enumerate(items[:5], 1):
            title_match = re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>", item)
            if not title_match:
                title_match = re.search(r"<title>(.*?)</title>", item)
            if title_match:
                headlines.append(f"{i}. {title_match.group(1).strip()}")

        if headlines:
            return "Here are the top BBC news headlines: " + ". ".join(headlines)
        return "I could not parse any headlines at this time."
    except Exception as e:
        return f"News fetch error: {e}"


def open_website(url: str) -> str:
    """Opens any website URL directly in the default web browser."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opening {url} in your browser."
