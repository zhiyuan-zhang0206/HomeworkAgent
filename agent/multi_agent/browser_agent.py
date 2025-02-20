from ..tools.files import read_file, write_file
from ..tools.browser import (
    browser_new_tab, 
    browser_click, 
    browser_understand_page, 
    browser_scroll, 
    browser_typewrite, 
    browser_hotkey, 
    check_browser_download_folder, 
    browser_list_tabs, 
    browser_switch_tab_to
)
from .member_agent import make_member_node


BROWSER_ROLE_PROMPT = """
You will act as a browser agent.
You can control the user's Chrome browser to perform tasks.
You will receive a prompt containing the task, and you need to operate the browser to perform the task.

After you arrive at new content (after clicking, opening new tabs, etc.), you should first use browser_understand_page to get a description of the page.

All user's credentials are already auto-filled in the browser.

Some tips:
1. Use 'Ctrl+J' to open the downloads page.
"""

BROWSER_AGENT_NAME = "browser_agent"

BROWSER_AGENT_ABILITIES = "browser_agent can control the user's Chrome browser completely, and can read or write pure text files."

browser_node = make_member_node(
    BROWSER_AGENT_NAME, 
    BROWSER_ROLE_PROMPT, 
    [
        browser_new_tab,
        browser_click, 
        browser_scroll, 
        browser_understand_page,
        browser_hotkey,
        browser_typewrite,
        browser_list_tabs,
        browser_switch_tab_to,
        check_browser_download_folder,
        read_file, 
        write_file
    ]
)
