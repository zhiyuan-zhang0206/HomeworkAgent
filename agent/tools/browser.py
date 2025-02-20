from typing import List
from langchain_core.tools import tool
from pathlib import Path
from loguru import logger
import time
from PIL import Image
import tempfile
from .files import get_file_tree
import win32api
import mss
import ctypes
def get_scaling_factor():
    """Returns the system's DPI scaling factor."""
    hdc = ctypes.windll.user32.GetDC(0)
    dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
    ctypes.windll.user32.ReleaseDC(0, hdc)
    return dpi / 96.0  # Default DPI is 96 (100%)

DOWNLOAD_FOLDER = "D:/zzy/Downloads/"
SCROLLBAR_COLOR = (193, 193, 193)
TRACK_COLOR = (241, 241, 241)

import pyautogui
import win32gui
from .clipboard_utils import safe_write, safe_read_clipboard
from .ocr import perform_ocr
from .vlm import get_image_description

class ChromeController:
    IMAGE_GRAB_MARGIN = int(8 * get_scaling_factor())
    CHROME_WINDOW_TOP_MARGIN = 122 # includes tabs, address bar, bookmarks bar
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.tabs = [{"address": "", "title": "New Tab"}]
            cls._instance.current_tab_index = 0
        return cls._instance

    def __init__(self):
        pass

    def _get_all_chrome_handles(self):
        chrome_handles = set()
        def callback(hwnd, handles):
            if "- Google Chrome" in win32gui.GetWindowText(hwnd):
                handles.add(hwnd)
            return True
        
        win32gui.EnumWindows(callback, chrome_handles)
        return chrome_handles

    def _open(self):
        try:
            existing_handles = self._get_all_chrome_handles()
            
            pyautogui.hotkey('win', 'r')
            time.sleep(0.5)
            safe_write('chrome --new-window')
            pyautogui.press('enter')
            time.sleep(1)
            pyautogui.hotkey('esc')
            new_handles = self._get_all_chrome_handles()
            new_handle = (new_handles - existing_handles).pop() if new_handles - existing_handles else None
            logger.info(f"New chrome window handle: {new_handle}")
            if new_handle:
                self.window_handle = new_handle
                time.sleep(0.5)
                return True

            return False
        except Exception as e:
            logger.error(f"Failed to open Chrome: {e}")
            return False

    def _get_window(self):
        if not hasattr(self, "window_handle"):
            self._open()
        def callback(hwnd, windows):
            if "- Google Chrome" in win32gui.GetWindowText(hwnd) and hwnd == self.window_handle:
                windows.append(hwnd)
            return True
        
        windows = []
        win32gui.EnumWindows(callback, windows)
        if not windows:
            raise Exception("Chrome window not found. Most probably it's closed.")
        return windows[0]

    def _ensure_chrome_topmost(self):
        chrome_window = self._get_window()
        time.sleep(0.1)
        try:
            win32gui.SetForegroundWindow(chrome_window)
        except Exception as e:
            logger.warning(f"Failed to set Chrome to topmost: {e}")
            pyautogui.hotkey('alt')
            time.sleep(0.1)
            win32gui.SetForegroundWindow(chrome_window)
            time.sleep(0.1)
            pyautogui.hotkey('alt')
            time.sleep(0.1)
        time.sleep(0.1)

    def _get_monitor_number(self):
        """Get the monitor number that contains the window."""
        monitor = win32api.MonitorFromWindow(self.window_handle)
        monitors = win32api.EnumDisplayMonitors()
        for i, (hMonitor, _, _) in enumerate(monitors):
            if hMonitor == monitor:
                logger.info(f"Monitor {i + 1} is the one containing the window")
                return i + 1  # mss uses 1-based monitor numbers
        logger.info(f"Fallback to primary monitor 1")
        return 1  # fallback to primary monitor

    def capture(self) -> Image.Image:
        logger.info("Capturing browser screenshot")
        self._ensure_chrome_topmost()
        chrome_window = self._get_window()
        window_bounds = win32gui.GetWindowRect(chrome_window)
        window_bounds = (window_bounds[0] + self.IMAGE_GRAB_MARGIN,
                         window_bounds[1] + self.IMAGE_GRAB_MARGIN,
                         window_bounds[2] - self.IMAGE_GRAB_MARGIN,
                         window_bounds[3] - self.IMAGE_GRAB_MARGIN)
        scaling_factor = get_scaling_factor()
        
        with mss.mss() as sct:
            monitor_number = self._get_monitor_number()
            monitor = sct.monitors[monitor_number]
            original_monitor = {
                "left": monitor["left"],
                "top": monitor["top"],
                "width": monitor["width"],
                "height": monitor["height"]
            }
            corrected_monitor = {
                "left": int(monitor["left"] / scaling_factor),
                "top": int(monitor["top"] / scaling_factor),
                "width": int(monitor["width"] / scaling_factor),
                "height": int(monitor["height"] / scaling_factor)
            }
            
            screen = sct.grab(corrected_monitor)
            screen_img = Image.frombytes('RGB', screen.size, screen.rgb)
            
            left = (window_bounds[0] - original_monitor["left"]) / scaling_factor
            top = (window_bounds[1] - original_monitor["top"]) / scaling_factor  + self.CHROME_WINDOW_TOP_MARGIN
            right = (window_bounds[2] - original_monitor["left"]) / scaling_factor
            bottom = (window_bounds[3] - original_monitor["top"]) / scaling_factor
            
            window_img = screen_img.crop((left, top, right, bottom))
        return window_img

    def new_tab(self, url:str=None)->str:
        logger.info(f"Opening new tab with url: {url}")
        self._ensure_chrome_topmost()
        pyautogui.hotkey('ctrl', 't')
        time.sleep(0.5)
        
        new_index = len(self.tabs)
        self.tabs.append({"address": url if url else "", "title": ""})
        self.current_tab_index = new_index
        
        if url:
            self._navigate_to(url)
        self._wait_for_page_load()
        self._update_current_tab_meta()
        return f"Opened new tab with address {self.tabs[self.current_tab_index]['address']}."

    def _navigate_to(self, url):
        logger.info(f"Navigating to address: {url}")
        self._ensure_chrome_topmost()
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.5)
        safe_write(url)
        pyautogui.press('enter')
        return f'Navigated to address {url}.'

    def switch_to_tab(self, index):
        logger.info(f"Switching to tab {index}")
        self._ensure_chrome_topmost()
        if 0 <= index < len(self.tabs):
            shifts = (index - self.current_tab_index) % len(self.tabs)
            for _ in range(shifts):
                pyautogui.hotkey('ctrl', 'tab')
            self.current_tab_index = index
            tab_meta = self.tabs[index]
            message = f'Switched to tab {index}, address {tab_meta["address"]}, title {tab_meta["title"]}.'
        else:
            message = f'Invalid tab index: {index}.'
        logger.info(message)
        return message

    def close_current_tab(self):
        logger.info(f"Closing current tab")
        self._ensure_chrome_topmost()
        closed_title = self.tabs[self.current_tab_index]['title']
        closed_address = self.tabs[self.current_tab_index]['address']
        pyautogui.hotkey('ctrl', 'w')
        time.sleep(0.5)
        self.tabs.pop(self.current_tab_index)
        self.switch_to_tab(0)
        current_title = self.tabs[self.current_tab_index]['title']
        current_address = self.tabs[self.current_tab_index]['address']
        message = (
            f'Closed current tab {closed_title} of address {closed_address}. '
            f'Current tab is tab 0 with title {current_title} and address {current_address}.'
        )
        logger.info(message)
        return message

    def _wait_for_page_load(self):
        time.sleep(10)  # TODO: implement this properly

    def _get_current_address(self):
        logger.info(f"Getting current tab's address")
        if not self.tabs:
            raise Exception("No tabs found")
        # ctrl + l
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.5)
        # copy, and read from clipboard
        address = safe_read_clipboard()
        # esc
        # pyautogui.hotkey('esc')
        logger.info(f"Got current tab's address: {address}")
        return address
        
    def _get_current_title(self):
        logger.info(f"Getting current tab's title")
        window = self._get_window()
        if window:
            title = win32gui.GetWindowText(window).removesuffix(" - Google Chrome")
            logger.info(f"Got current tab's title: {title}")
            return title
        raise Exception("Chrome window not found")

    def get_tabs(self):
        tabs_str = "\n".join([f"{i}: {tab}" for i, tab in enumerate(self.tabs)])
        logger.info(f"Getting tabs:\n{tabs_str}")
        return list(enumerate(self.tabs))

    def _update_current_tab_meta(self):
        address = self._get_current_address()
        title = self._get_current_title()
        self.tabs[self.current_tab_index] = {"address": address, "title": title}

    def typewrite(self, text):
        self._ensure_chrome_topmost()
        safe_write(text)

    def hotkey(self, *keys):
        logger.info(f"Pressing hotkey: {keys}")
        self._ensure_chrome_topmost()
        pyautogui.hotkey(*keys)
        self._wait_for_page_load()
        self._update_current_tab_meta()

    def click(self, x, y):
        x = int(x)
        y = int(y)
        logger.info(f"Trying to click at ({x}, {y})")
        self._ensure_chrome_topmost()
        chrome_window = self._get_window()
        left, top, right, bottom = win32gui.GetWindowRect(chrome_window)
        scaling_factor = get_scaling_factor()
        abs_x = int(x * scaling_factor) + left
        abs_y = int((y + self.CHROME_WINDOW_TOP_MARGIN )* scaling_factor) + top

        pyautogui.click(abs_x, abs_y)
        logger.info(f'Input: {x}, {y}. Clicked at ({abs_x}, {abs_y}).')
        self._wait_for_page_load()
        self._update_current_tab_meta()

    def get_current_tab_meta(self):
        return self.tabs[self.current_tab_index]

    def back(self):
        """Navigate back in browser history."""
        logger.info("Navigating back")
        self._ensure_chrome_topmost()
        pyautogui.hotkey('alt', 'left')
        self._wait_for_page_load()
        self._update_current_tab_meta()
        return f'Navigated back. Title: {self.tabs[self.current_tab_index]["title"]}, Address: {self.tabs[self.current_tab_index]["address"]}'

    def forward(self):
        """Navigate forward in browser history."""
        logger.info("Navigating forward")
        self._ensure_chrome_topmost()
        pyautogui.hotkey('alt', 'right')
        self._wait_for_page_load()
        self._update_current_tab_meta()
        return f'Navigated forward. Title: {self.tabs[self.current_tab_index]["title"]}, Address: {self.tabs[self.current_tab_index]["address"]}'

@tool
def browser_capture(save_path:str)->str:
    '''
    Capture a screenshot of the Chrome browser.

    Args:
        save_path: Optional. The path to save the screenshot.
    '''
    chrome = ChromeController()
    image = chrome.capture()
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    image.save(save_path)
    message = f"Captured browser screenshot and saved to {save_path}"
    logger.info(message)
    return message

@tool
def browser_new_tab(url:str, understand_page:bool=True)->str:
    '''
    Open a new tab in the Chrome browser.

    Args:
        url: str
            The URL to navigate to in the new tab.
        understand_page: bool
            Whether to also understand the page. This calls the tool browser_understand_page.
    '''
    chrome = ChromeController()
    message = chrome.new_tab(url)
    logger.info(message)
    all_tab_info = str(browser_list_tabs.invoke({}))
    current_tab_info = str(chrome.get_current_tab_meta())
    message += "\n\nAll tabs:\n" + all_tab_info + "\n\nCurrent tab:\n" + current_tab_info
    if understand_page:
        page_info = browser_understand_page.invoke({})
        message += "\n\n" + page_info
    return message

@tool
def browser_list_tabs():
    '''
    Get the list of tabs.
    '''
    chrome = ChromeController()
    tabs = chrome.get_tabs()
    logger.info(f"Got tabs: {tabs}")
    return str(tabs)

@tool
def browser_switch_tab_to(index):
    '''
    Switch to a specific tab by index.

    Args:
        index: int
            The index of the tab to switch to.
    '''
    chrome = ChromeController()
    result = chrome.switch_to_tab(index)
    return result

# @tool
# def browser_close_current_tab():
#     '''
#     Close the current tab in the Chrome browser.
#     '''
#     chrome = ChromeController()
#     result = chrome.close_current_tab()
#     return result

@tool
def browser_click(x:int, y:int, understand_page:bool=True)->str:
    '''
    Click at (x, y).

    Args:
        x: int
            The x coordinate to click at.
        y: int
            The y coordinate to click at.
        understand_page: bool
            Whether to also understand the page. This calls the tool browser_understand_page. Default to True.
    '''
    chrome = ChromeController()
    chrome.click(x, y)
    if understand_page:
        page_info = browser_understand_page.invoke({})
        return f'Clicked at ({x}, {y}).\n\n{page_info}'
    all_tab_info = str(browser_list_tabs.invoke({}))
    current_tab_info = str(chrome.get_current_tab_meta())
    return f'Clicked at ({x}, {y}).\nAll tabs:\n{all_tab_info}\n\nCurrent tab:\n{current_tab_info}'

@tool
def browser_hotkey(keys:str, understand_page:bool=True)->str:
    '''
    Press hotkey(s). Common choices: ['pgdn'] for scrolling down, ['f5'] for refreshing the page.

    Args:
        keys: str
            The keys to press, in pyautogui style, e.g. 'ctrl,c', 'pgdn'. Use comma to separate multiple keys.
        understand_page: bool
            Whether to also understand the page. This calls the tool browser_understand_page.
    '''
    keys = [key.strip() for key in keys.split(',')]
    chrome = ChromeController()
    chrome.hotkey(*keys)
    if understand_page:
        page_info = browser_understand_page.invoke({})
        return f'Pressed hotkey: {keys}.\n\n{page_info}'
    return f'Pressed hotkey: {keys}.'

@tool
def browser_scroll(direction:str, understand_page:bool=True)->str:
    '''
    Scroll in the given direction.

    Args:
        direction: str
            The direction to scroll, either 'up' or 'down'. Each scroll scrolls to next page.
        understand_page: bool
            Whether to also understand the page. This calls the tool browser_understand_page.
    '''
    chrome = ChromeController()
    chrome.hotkey('pgdn' if direction == 'down' else 'pgup')
    if understand_page:
        page_info = browser_understand_page.invoke({})
        return f'Scrolled {direction}.\n\n{page_info}'
    return f'Scrolled {direction}.'

@tool
def browser_typewrite(text:str)->str:
    '''
    Typewrite text.

    Args:
        text: str
            The text to typewrite.
    '''
    chrome = ChromeController()
    chrome.typewrite(text)
    return f'Typed in {len(text)} characters.'

@tool
def browser_understand_page():
    '''
    Get a understanding of the current page.
    Returns: 1. Page range (start-end tuple, (0,1) means the whole page, (0, 0.6) means the top 60% of the page is visible, need to scroll down to see the rest), 2. Page description, 3. Text elements found (with positions)
    '''
    chrome = ChromeController()
    screenshot = chrome.capture()

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        temp_path = tmp.name
        screenshot.save(temp_path)
    logger.info(f"Saved screenshot to temp file {temp_path}")
    ocr_results = str(perform_ocr.invoke({"image_path": temp_path}))

    image_description = get_image_description.invoke({
        "filepath": temp_path,
        "additional_prompt": (
            "The image is a screenshot of the Chrome browser. First check if there's a vertical scrollbar - "
            "if present, estimate its position. Describe what portion of the page is visible (top/middle/bottom), "
            "and whether scrolling down would be needed to see more content. Then describe the page content."
        )
    })
    result = ""
    result += "Page Description:\n"
    result += image_description
    result += "\n\n"
    result += "Text elements found (with positions):\n"
    result += ocr_results

    return result

@tool
def check_browser_download_folder():
    '''
    Check the browser download folder.
    '''
    result = get_file_tree.invoke({
        "root_path": DOWNLOAD_FOLDER,
        "sort_by": "modified",
        "max_depth": 1,
        "max_file_each_folder": 5,
        "max_folder_each_folder": 0
    })
    return result

@tool
def check_browser_download_page():
    '''
    Check the Chrome browser download page.
    '''
    chrome = ChromeController()
    chrome.hotkey('ctrl', 'j')
    return "Opened Chrome download page."

@tool
def browser_back(understand_page:bool=True)->str:
    '''
    Navigate back in browser history.

    Args:
        understand_page: bool
            Whether to also understand the page. This calls the tool browser_understand_page.
    '''
    chrome = ChromeController()
    message = chrome.back()
    if understand_page:
        page_info = browser_understand_page.invoke({})
        return f'{message}\n\n{page_info}'
    return message

@tool
def browser_forward(understand_page:bool=True)->str:
    '''
    Navigate forward in browser history.

    Args:
        understand_page: bool
            Whether to also understand the page. This calls the tool browser_understand_page.
    '''
    chrome = ChromeController()
    message = chrome.forward()
    if understand_page:
        page_info = browser_understand_page.invoke({})
        return f'{message}\n\n{page_info}'
    return message

__all__ = [
    'browser_capture', 
    'browser_new_tab', 
    'browser_switch_tab_to', 
    'browser_typewrite',
    'check_browser_download_folder',
    'browser_list_tabs',
    'browser_click',
    'browser_hotkey',
    "browser_understand_page",
    "check_browser_download_page",
    "browser_back",
    "browser_forward",
]