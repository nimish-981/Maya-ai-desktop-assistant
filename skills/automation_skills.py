"""
skills/automation_skills.py

Automation tools: typing, clicking, and application control.
These functions are auto-registered as Groq tools via engine.py.
"""
import os
import time


def _open_program(app_name: str) -> str:
    """Opens a program using the Windows start command or Windows Search."""
    try:
        os.system(f"start {app_name}")
        return f"Opening {app_name}."
    except Exception as e:
        return f"Could not open {app_name}: {e}"


def type_message(message: str) -> str:
    """Types text or instructions into the currently focused window or text box."""
    import pyautogui
    import pyperclip
    import time
    try:
        pyautogui.FAILSAFE = False
        time.sleep(0.5)
        pyperclip.copy(message)
        pyautogui.hotkey('ctrl', 'v')
        return f"Successfully typed: {message}"
    except Exception as e:
        try:
            pyautogui.write(message, interval=0.02)
            return f"Successfully typed: {message}"
        except Exception as e2:
            return f"Could not type message: {e2}"


def click_position(x: str, y: str) -> str:
    """Moves the mouse to the specified X, Y screen coordinates and clicks. Example: x='500', y='300'."""
    import pyautogui
    try:
        xi, yi = int(x), int(y)
        pyautogui.click(xi, yi)
        return f"Clicked at position ({xi}, {yi})."
    except Exception as e:
        return f"Could not click at ({x}, {y}): {e}"


def scroll_page(direction: str, amount: str) -> str:
    """Scrolls the current window up or down. Direction: 'up' or 'down'. Amount: number of scroll clicks."""
    import pyautogui
    try:
        clicks = int(''.join(filter(str.isdigit, amount)) or '3')
        if "up" in direction.lower():
            pyautogui.scroll(clicks)
            return f"Scrolled up {clicks} times."
        else:
            pyautogui.scroll(-clicks)
            return f"Scrolled down {clicks} times."
    except Exception as e:
        return f"Scroll error: {e}"


def switch_window() -> str:
    """Switches to the next open window using Alt+Tab."""
    import pyautogui
    try:
        pyautogui.hotkey('alt', 'tab')
        return "Switched to the next window."
    except Exception as e:
        return f"Could not switch window: {e}"


def close_window() -> str:
    """Closes the currently active window using Alt+F4."""
    import pyautogui
    try:
        pyautogui.hotkey('alt', 'f4')
        return "Closed the active window."
    except Exception as e:
        return f"Could not close window: {e}"