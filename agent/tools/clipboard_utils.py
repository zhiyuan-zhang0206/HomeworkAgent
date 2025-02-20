import time
import pyautogui
import pyperclip

def safe_write(text: str) -> None:
    """Safely write text using clipboard, preserving original clipboard content."""
    # Store original clipboard content
    original = pyperclip.paste()
    
    try:
        # Copy new text to clipboard
        pyperclip.copy(text)
        time.sleep(0.1)  # Small delay to ensure clipboard is updated
        # Paste the text
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.1)
    finally:
        # Restore original clipboard content
        pyperclip.copy(original)

def safe_read_clipboard() -> str:
    """Safely read clipboard content, preserving original clipboard content."""
    original = pyperclip.paste()
    # ctrl + c
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.1)
    result = pyperclip.paste()
    # restore original clipboard content
    pyperclip.copy(original)
    return result
