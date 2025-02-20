from ..tools.vlm import get_image_description
from ..tools.ocr import perform_ocr, locate_text
from ..tools.communication import get_latest_email, send_email_to_user, send_email
from ..tools.files import write_file, read_file, get_file_tree
from ..tools.terminals import open_terminal, command_terminal, get_terminal_output, close_terminal, rename_terminal, list_all_terminals
from ..tools.browser import (
    browser_new_tab, browser_click, browser_understand_page, browser_scroll, 
    browser_typewrite, browser_hotkey, check_browser_download_folder, 
    browser_switch_tab_to, browser_list_tabs
)
from ..tools.pdf2md import convert_pdf2md
from ..tools.files import rename_file
from ..tools.memory import search_memory, add_memory, delete_memory, update_memory
from ..tools.notify_supervisor import notify_supervisor
# from ..tools.wechat import send_message, get_all_new_messages

MEMORY_RETRIEVAL_TRIGGER_TOOLS = [
    get_file_tree,
    read_file,

    get_latest_email,

    perform_ocr,
    locate_text,
    get_image_description,

    get_terminal_output,

    browser_understand_page,
    convert_pdf2md,

    # send_message,
    # get_all_new_messages,
]
MEMORY_RETRIEVAL_TRIGGER_TOOL_NAMES = [tool.name for tool in MEMORY_RETRIEVAL_TRIGGER_TOOLS]

MEMORY_RETRIEVAL_NO_TRIGGER_TOOLS = [
    open_terminal,
    command_terminal,
    close_terminal,
    rename_terminal,
    list_all_terminals,

    browser_new_tab,
    browser_click,
    browser_scroll,
    browser_typewrite,
    browser_hotkey,
    browser_switch_tab_to,
    browser_list_tabs,
    check_browser_download_folder,
    
    write_file,
    rename_file,

    search_memory,
    add_memory,
    delete_memory,
    update_memory,
    
    notify_supervisor,
    send_email_to_user,
    send_email,
]
MEMORY_RETRIEVAL_NO_TRIGGER_TOOL_NAMES = [tool.name for tool in MEMORY_RETRIEVAL_NO_TRIGGER_TOOLS]

# assert empty intersection
assert not set(MEMORY_RETRIEVAL_TRIGGER_TOOL_NAMES) & set(MEMORY_RETRIEVAL_NO_TRIGGER_TOOL_NAMES)

def is_trigger_memory_tool(tool_name: str) -> bool:
    if tool_name in MEMORY_RETRIEVAL_TRIGGER_TOOL_NAMES:
        return True
    elif tool_name in MEMORY_RETRIEVAL_NO_TRIGGER_TOOL_NAMES:
        return False
    else:
        raise ValueError(f"Tool {tool_name} not found in MEMORY_RETRIEVAL_TRIGGER_TOOLS or MEMORY_RETRIEVAL_NO_TRIGGER_TOOLS")

__all__ = ['is_trigger_memory_tool']
