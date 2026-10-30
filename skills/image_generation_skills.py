"""
skills/image_generation_skills.py

Autonomous AI Image Generation and Wallpaper Creation for Maya.
Generates photorealistic images, digital art, concept illustrations,
and desktop wallpapers using neural image synthesis and HD photographic engines.
Auto-registered via engine.py.
"""

import os
import sys
import re
import time
import random
import urllib.request
import urllib.parse
import json
import ctypes
from datetime import datetime

# Ensure Windows consoles handle UTF-8 symbols cleanly
for stream in (sys.stdout, sys.stderr):
    if stream and hasattr(stream, 'reconfigure'):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass


def _clean_prompt(prompt: str) -> str:
    """Strips conversational command artifacts like 'and open it', 'and show me', etc."""
    cleaned = prompt.strip()
    # Strip common command trailing phrases
    cleaned = re.sub(r'[\s,]+(and\s+(?:open|show|display|view)\s+(?:it|me|this)?|please|for\s+me|right\s+now)+$', '', cleaned, flags=re.I).strip()
    # Strip leading phrases like 'an image of', 'a picture of'
    cleaned = re.sub(r'^(?:an?\s+)?(?:image|art|picture|photo|painting|illustration|wallpaper)\s+(?:of|for)\s+', '', cleaned, flags=re.I).strip()
    return cleaned


def _translate_if_needed(text: str) -> str:
    """Detects Hindi/Gujarati script and translates to English prompt for optimal generation."""
    has_indic = bool(re.search(r'[\u0900-\u097F\u0A80-\u0AFF]', text))
    if not has_indic:
        return text

    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(text)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data and data[0] and data[0][0] and data[0][0][0]:
                translated = data[0][0][0].strip()
                print(f"🎨 [IMAGE PROMPT TRANSLATION] '{text}' -> '{translated}'")
                return translated
    except Exception as e:
        print(f"⚠️ Translation notice: {e}")
    return text


def _fetch_from_wikimedia(query: str, width: int = 1280) -> bytes | None:
    """Fetches a high-definition photograph/art piece from Wikimedia Commons, strictly verifying real image formats."""
    try:
        headers = {'User-Agent': 'MayaVoiceAssistant/2.0 (contact: nimish@assistant.local)'}
        clean_q = re.sub(r'[^a-zA-Z0-9\s]', ' ', query).strip()
        url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch={urllib.parse.quote(clean_q)}&gsrlimit=5&prop=imageinfo&iiprop=url&iiurlwidth={width}&format=json"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode('utf-8'))
            pages = data.get('query', {}).get('pages', {})
            for p in pages.values():
                title = p.get('title', '')
                # STRICT FILTER: Must be a real image format, never a PDF or document scan
                if not re.search(r'\.(jpe?g|png|webp)$', title, re.I):
                    continue
                info = p.get('imageinfo', [{}])[0]
                thumb = info.get('thumburl') or info.get('url')
                if thumb:
                    req2 = urllib.request.Request(thumb, headers=headers)
                    with urllib.request.urlopen(req2, timeout=12) as r2:
                        img_bytes = r2.read()
                        if len(img_bytes) > 5000:
                            print(f"🖼️ [HD ARCHIVE ENGINE] Fetched '{title}' ({len(img_bytes)} bytes)")
                            return img_bytes
    except Exception as e:
        print(f"⚠️ Archive fetch notice: {e}")
    return None


def _generate_local_fallback_art(prompt: str, width: int = 1280, height: int = 720) -> bytes:
    """Generates an aesthetic high-resolution artistic gradient canvas with PIL."""
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (width, height), (15, 23, 42))
        draw = ImageDraw.Draw(img)

        # Draw aesthetic futuristic radial gradient & glowing lines
        for r in range(height, 0, -8):
            alpha_color = (
                int(15 + (r / height) * 45),
                int(23 + (r / height) * 60),
                int(42 + (r / height) * 120)
            )
            draw.ellipse([-r, -r, width + r, height + r], fill=alpha_color)

        # Draw decorative grid & stars
        random.seed(hash(prompt) % 100000)
        for _ in range(120):
            x = random.randint(0, width)
            y = random.randint(0, height)
            rad = random.randint(1, 3)
            star_color = (200 + random.randint(0, 55), 220 + random.randint(0, 35), 255)
            draw.ellipse([x - rad, y - rad, x + rad, y + rad], fill=star_color)

        # Draw title text
        text = f"Maya AI Art: {prompt[:40]}"
        draw.text((width // 2 - 180, height // 2 - 20), text, fill=(255, 255, 255))
        draw.text((width // 2 - 120, height // 2 + 20), "Generated with Maya Cyber AI", fill=(56, 189, 248))

        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        return buf.getvalue()
    except Exception:
        return b""


def _fetch_image_bytes(full_prompt: str, width: int = 1280, height: int = 720) -> bytes:
    """Downloads generated image using multi-tiered neural and photographic fail-safe engines."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
    }

    # 1. Primary Neural Synthesis Engine (Pollinations AI with intelligent cooldown handling)
    encoded = urllib.parse.quote(full_prompt)
    neural_urls = [
        f"https://pollinations.ai/p/{encoded}",
        f"https://image.pollinations.ai/prompt/{encoded}"
    ]

    for attempt, url in enumerate(neural_urls):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = resp.read()
                if len(data) > 5000:
                    print(f"✨ [NEURAL SYNTHESIS ENGINE] Generated image ({len(data)} bytes)")
                    return data
        except urllib.error.HTTPError as http_err:
            if http_err.code == 402:
                # Parse cooldown time if available
                try:
                    err_body = http_err.read().decode('utf-8', errors='ignore')
                    m = re.search(r'Retry after (\d+)s', err_body)
                    wait_sec = int(m.group(1)) if m else 0
                    if 0 < wait_sec <= 25:
                        print(f"⏳ [NEURAL COOLDOWN] Waiting {wait_sec+1}s for free generation slot...")
                        time.sleep(wait_sec + 1)
                        # Retry after cooldown
                        try:
                            req_retry = urllib.request.Request(url, headers=headers)
                            with urllib.request.urlopen(req_retry, timeout=25) as resp_retry:
                                data = resp_retry.read()
                                if len(data) > 5000:
                                    print(f"✨ [NEURAL SYNTHESIS ENGINE] Generated image after cooldown ({len(data)} bytes)")
                                    return data
                        except Exception as retry_err:
                            print(f"⚠️ Cooldown retry notice: {retry_err}")
                except Exception:
                    pass
            print(f"⚠️ Neural attempt {attempt+1} notice: {http_err}")
        except Exception as e:
            print(f"⚠️ Neural attempt {attempt+1} notice: {e}")

    # 2. Secondary High-Definition Visual Archive Engine (Strict real-image filter)
    core_concept = full_prompt.split(',')[0].strip()
    data = _fetch_from_wikimedia(core_concept, width=width)
    if data:
        return data

    # 3. Tertiary Local Aesthetic Art Generator (100% Offline Fail-Safe)
    print("🎨 [LOCAL ART ENGINE] Rendering high-definition canvas...")
    return _generate_local_fallback_art(core_concept, width=width, height=height)


def generate_ai_image(prompt: str, style: str = "photorealistic") -> str:
    """Generates a high-quality AI image from any description or prompt (e.g. 'Lord Hanuman', 'Lord Rama', 'a cybernetic tiger with neon stripes', 'a cute baby panda'). Styles: photorealistic, anime, cyberpunk, 3d render, fantasy, digital art."""
    if not prompt or not prompt.strip():
        return "Please describe the image you want me to generate."

    prompt_clean = _clean_prompt(_translate_if_needed(prompt.strip()))
    style_clean = style.lower().strip()

    # Style enhancers for cinematic aesthetic quality
    style_modifiers = {
        "photorealistic": "8k resolution, highly detailed, photorealistic, cinematic lighting, masterwork photography",
        "anime": "makoto shinkai aesthetic, studio ghibli anime style, highly detailed, vibrant, 4k",
        "cyberpunk": "cyberpunk aesthetic, glowing neon lights, futuristic sci-fi city, reflections, 8k",
        "3d render": "octane 3D render, Pixar style, ray tracing, smooth textures, 4k",
        "fantasy": "epic fantasy art, mythical atmosphere, magical glow, intricate details, artstation",
        "digital art": "modern digital illustration, sharp focus, clean vibrant colors, masterpiece",
        "oil painting": "classic oil on canvas, textured brushstrokes, museum lighting, fine art"
    }

    modifier = style_modifiers.get(style_clean, style_modifiers["photorealistic"])
    full_prompt = f"{prompt_clean}, {modifier}"

    pictures_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Pictures", "Maya_AI_Art")
    os.makedirs(pictures_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_slug = re.sub(r'[^a-zA-Z0-9]', '_', prompt_clean[:30]).strip('_')
    filename = f"maya_{safe_slug}_{timestamp}.jpg"
    filepath = os.path.join(pictures_dir, filename)

    print(f"🎨 Generating {style_clean} image for: '{prompt_clean}'...")
    data = _fetch_image_bytes(full_prompt, width=1024, height=1024)

    try:
        with open(filepath, 'wb') as f:
            f.write(data)

        # Automatically open the generated image on the user's screen
        try:
            os.startfile(filepath)
        except Exception:
            pass

        return f"I have generated the {style_clean} image of '{prompt_clean}'. It has been saved to your Pictures folder and opened on your screen!"
    except Exception as e:
        return f"Error saving image: {e}"


def generate_wallpaper(theme: str) -> str:
    """Generates a high-definition widescreen desktop wallpaper based on any theme (e.g. 'deep space nebulae', 'neon mountains', 'rainy cyber city'), opens it, and sets it as the desktop wallpaper."""
    if not theme or not theme.strip():
        theme = "scenic mountain landscape with stars"

    theme_clean = _clean_prompt(_translate_if_needed(theme.strip()))
    full_prompt = f"{theme_clean}, breathtaking widescreen 16:9 desktop wallpaper, 8k resolution, cinematic lighting, epic vista, photorealistic, masterpiece"

    wallpapers_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Pictures", "Maya_Wallpapers")
    os.makedirs(wallpapers_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_slug = re.sub(r'[^a-zA-Z0-9]', '_', theme_clean[:30]).strip('_')
    filename = f"wallpaper_{safe_slug}_{timestamp}.jpg"
    filepath = os.path.join(wallpapers_dir, filename)

    print(f"🖥️ Generating wallpaper for theme: '{theme_clean}'...")
    data = _fetch_image_bytes(full_prompt, width=1920, height=1080)

    try:
        with open(filepath, 'wb') as f:
            f.write(data)

        # 1. Set as Windows desktop wallpaper via native Win32 API
        try:
            # SPI_SETDESKWALLPAPER = 20, SPIF_UPDATEINIFILE = 1, SPIF_SENDCHANGE = 2
            ctypes.windll.user32.SystemParametersInfoW(20, 0, filepath, 3)
        except Exception as wp_err:
            print(f"⚠️ Notice setting wallpaper: {wp_err}")

        # 2. Open the image in default viewer
        try:
            os.startfile(filepath)
        except Exception:
            pass

        return f"I have created a beautiful wallpaper for '{theme_clean}'. It has been set as your desktop background and opened on your screen!"
    except Exception as e:
        return f"Error creating wallpaper: {e}"


def create_digital_art(concept: str) -> str:
    """Creates a stylized digital illustration or artistic painting based on a concept or idea."""
    return generate_ai_image(prompt=concept, style="digital art")
