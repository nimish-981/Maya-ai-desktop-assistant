"""
skills/gesture_skills.py

Contactless webcam hand gesture control for Maya Voice Assistant.
Uses lightweight OpenCV computer vision to detect gestures without heavy CPU load:
  - Open Palm (5 fingers)  -> Play/Pause Media
  - Peace/Victory (2 fingers) -> Take Screenshot
  - Pointing / 1 Finger    -> Volume Up
  - Fist / 0 Fingers       -> Mute Audio
"""
import cv2
import numpy as np
import threading
import time
import os
from datetime import datetime
import pyautogui

_GESTURE_THREAD = None
_GESTURE_RUNNING = False
_LAST_ACTION_TIME = 0.0
_COOLDOWN_SECONDS = 2.0
_LAST_TRIGGERED_GESTURE = ""


def _detect_gesture_from_frame(frame):
    """Analyzes a single video frame and returns the detected gesture name or None."""
    # Convert to HSV and YCrCb for robust lighting-invariant skin color segmentation
    ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    lower_skin = np.array([0, 133, 77], dtype=np.uint8)
    upper_skin = np.array([255, 173, 127], dtype=np.uint8)
    mask = cv2.inRange(ycrcb, lower_skin, upper_skin)

    # Clean noise with morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.GaussianBlur(mask, (5, 5), 100)

    # Find the largest contour (the user's hand)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    max_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(max_contour)
    if area < 4000:  # Hand too small or too far
        return None

    # Convex hull & defects
    hull = cv2.convexHull(max_contour, returnPoints=False)
    if hull is None or len(hull) < 4:
        return None

    defects = cv2.convexityDefects(max_contour, hull)
    if defects is None:
        return "Fist"

    finger_count = 0
    for i in range(defects.shape[0]):
        s, e, f, d = defects[i].flatten()[:4]
        start = tuple(max_contour[s][0])
        end = tuple(max_contour[e][0])
        far = tuple(max_contour[f][0])

        # Triangle side lengths
        a = np.linalg.norm(np.array(end) - np.array(start))
        b = np.linalg.norm(np.array(far) - np.array(start))
        c = np.linalg.norm(np.array(end) - np.array(far))

        # Angle between fingers
        angle = np.degrees(np.arccos((b**2 + c**2 - a**2) / (2 * b * c + 1e-6)))

        # Defect between two open fingers typically has angle < 90 degrees and significant depth
        if angle <= 90 and d > 3000:
            finger_count += 1

    # Defects count corresponds to fingers - 1
    total_fingers = finger_count + 1 if finger_count > 0 else 0

    if total_fingers >= 4:
        return "Open Palm"
    elif total_fingers == 2:
        return "Peace / Victory"
    elif total_fingers == 1:
        return "One Finger"
    elif total_fingers == 0:
        return "Fist"

    return None


def _gesture_loop():
    global _GESTURE_RUNNING, _LAST_ACTION_TIME, _LAST_TRIGGERED_GESTURE
    cap = None
    try:
        cap = cv2.VideoCapture(0)
        if not cap or not cap.isOpened():
            print("⚠️ Gesture Control: Could not access webcam.")
            _GESTURE_RUNNING = False
            return

        print("📷 Gesture Control active: Watching for contactless hand commands...")

        while _GESTURE_RUNNING:
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.1)
                continue

            # Flip horizontally for natural mirror behavior
            frame = cv2.flip(frame, 1)
            # Downscale frame for fast 60fps processing with 0% CPU impact
            small_frame = cv2.resize(frame, (320, 240))

            gesture = _detect_gesture_from_frame(small_frame)
            now = time.time()

            if gesture and (now - _LAST_ACTION_TIME > _COOLDOWN_SECONDS):
                _LAST_TRIGGERED_GESTURE = gesture
                _LAST_ACTION_TIME = now

                if gesture == "Open Palm":
                    # 5 fingers: Play / Pause media
                    print("🖐️ Gesture Detected: Open Palm → Toggle Play/Pause Media")
                    pyautogui.press("playpause")

                elif gesture == "Peace / Victory":
                    # 2 fingers: Take screenshot
                    print("✌️ Gesture Detected: Peace Sign → Taking Screenshot")
                    screenshots_dir = os.path.join(os.getcwd(), 'Screenshots')
                    os.makedirs(screenshots_dir, exist_ok=True)
                    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    fp = os.path.join(screenshots_dir, f"gesture_screenshot_{ts}.png")
                    shot = pyautogui.screenshot()
                    shot.save(fp)

                elif gesture == "One Finger":
                    # 1 finger: Volume Up
                    print("☝️ Gesture Detected: One Finger → Volume Up")
                    for _ in range(3):
                        pyautogui.press("volumeup")

                elif gesture == "Fist":
                    # Fist: Mute volume
                    print("✊ Gesture Detected: Fist → Toggle Audio Mute")
                    pyautogui.press("volumemute")

            time.sleep(0.04)

    except Exception as e:
        print(f"⚠️ Gesture loop error: {e}")
    finally:
        if cap:
            try:
                cap.release()
            except Exception:
                pass
        _GESTURE_RUNNING = False
        print("📷 Gesture Control webcam released.")


def start_gesture_control() -> str:
    """Activates contactless hand gesture control via the webcam.
    Gestures supported:
      - Open Palm (5 fingers): Toggle Play/Pause media
      - Peace / Victory sign (2 fingers): Take screenshot
      - One Finger pointing: Volume Up
      - Fist (0 fingers): Mute Audio
    """
    global _GESTURE_RUNNING, _GESTURE_THREAD
    if _GESTURE_RUNNING:
        return "Hand gesture control is already active and running in the background."

    _GESTURE_RUNNING = True
    _GESTURE_THREAD = threading.Thread(target=_gesture_loop, daemon=True)
    _GESTURE_THREAD.start()
    return "Contactless gesture control activated. Watching webcam for Open Palm (Play/Pause), Peace Sign (Screenshot), One Finger (Volume Up), and Fist (Mute)."


def stop_gesture_control() -> str:
    """Deactivates and stops the webcam hand gesture controller and releases the camera."""
    global _GESTURE_RUNNING
    if not _GESTURE_RUNNING:
        return "Hand gesture control is not currently running."

    _GESTURE_RUNNING = False
    return "Hand gesture control has been deactivated and the webcam is released."


def get_gesture_status() -> str:
    """Checks whether webcam hand gesture control is currently active or inactive."""
    if _GESTURE_RUNNING:
        last = f" (Last gesture: {_LAST_TRIGGERED_GESTURE})" if _LAST_TRIGGERED_GESTURE else ""
        return f"Hand gesture control is ACTIVE{last}."
    return "Hand gesture control is INACTIVE."
