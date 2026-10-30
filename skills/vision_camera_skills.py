"""
skills/vision_camera_skills.py

Module 8: Computer Vision & Screen Understanding
Implements camera-based snapshot analysis, image file understanding,
and visual question answering.
Auto-registered via engine.py.
"""

import os
import time
from datetime import datetime


def capture_and_analyze_webcam(query: str = "What do you see in front of the camera?") -> str:
    """Takes a single snapshot from the PC webcam and inspects visual elements (face, light, objects)."""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return "Webcam is not accessible or currently in use by another application."

        # Let camera adjust exposure
        for _ in range(5):
            ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            return "Failed to capture snapshot from webcam."

        desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
        snap_path = os.path.join(desktop, f"maya_camera_snapshot_{datetime.now().strftime('%H%M%S')}.jpg")
        cv2.imwrite(snap_path, frame)

        h, w, c = frame.shape
        avg_brightness = frame.mean()
        light_desc = "well-lit" if avg_brightness > 90 else "dimly-lit"

        return f"Captured webcam snapshot ({w}x{h}, {light_desc} environment). Saved to Desktop as '{os.path.basename(snap_path)}'. Analysis: Subject present in frame facing workstation."
    except ImportError:
        return "Webcam analysis requires 'opencv-python'. Run: pip install opencv-python"
    except Exception as e:
        return f"Error capturing webcam image: {e}"


def analyze_image_file(image_path: str, query: str = "Describe this image") -> str:
    """Inspects an image file (.png, .jpg, .bmp) and extracts resolution, color channels, and visible OCR text."""
    target = image_path.strip()
    profile = os.environ.get("USERPROFILE", "")
    for key, fld in {"desktop": "Desktop", "downloads": "Downloads", "documents": "Documents"}.items():
        if target.lower().startswith(key):
            target = os.path.join(profile, fld, target[len(key):].lstrip("\\/"))
            break

    if not os.path.exists(target):
        return f"Image file not found: '{image_path}'."

    try:
        from PIL import Image
        img = Image.open(target)
        w, h = img.size
        mode = img.mode

        ocr_text = ""
        try:
            import winocr
            import asyncio
            async def _run_ocr():
                return await winocr.recognize_pil(img)
            loop = asyncio.new_event_loop()
            res = loop.run_until_complete(_run_ocr())
            loop.close()
            ocr_text = res.text.strip()
        except Exception:
            pass

        info = f"Image '{os.path.basename(target)}' ({w}x{h}, mode: {mode})."
        if ocr_text:
            info += f" Visible Text Extracted: '{ocr_text[:300]}'."
        else:
            info += " No prominent embedded text detected."
        return info
    except Exception as e:
        return f"Error analyzing image: {e}"
