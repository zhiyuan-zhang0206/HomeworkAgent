from pathlib import Path
import os
from typing import Literal
from langchain_core.tools import tool
from loguru import logger

@tool
def get_file_tree(root_path: str, 
                  max_depth: int = 2, 
                  max_file_each_folder: int = 20, 
                  max_folder_each_folder: int = 20,
                  sort_by: Literal['name', 'modified'] = 'name',
                  )->str:
    """
    Get the file tree of the directory.

    Args:
        root_path: str
            The root path of the file tree.
        max_depth: int, default 2
            The maximum depth of the file tree. Passing -1 means no limit.
        max_file_each_folder: int, default 20
            The maximum number of files in each folder. Passing -1 means no limit.
        max_folder_each_folder: int, default 20
            The maximum number of folders in each folder. Passing -1 means no limit.
        sort_by: Literal['name', 'modified'], default 'name'
            How to sort the files and folders. Options: 'name' (alphabetical) or 'modified' (last modified time)
    """
    if max_depth == -1:
        max_depth = float('inf')
    if max_file_each_folder == -1:
        max_file_each_folder = float('inf')
    if max_folder_each_folder == -1:
        max_folder_each_folder = float('inf')

    def tree(path, depth):
        if depth > max_depth:
            return []

        items = []
        try:
            contents = os.listdir(path)
            if sort_by == 'modified':
                contents.sort(key=lambda x: os.path.getmtime(os.path.join(path, x)), reverse=True)
            else:  # sort_by == 'name'
                contents.sort()
        except PermissionError:
            return ["[Permission Denied]"]

        # Get all items and mark them as folder or file
        all_items = [(item, os.path.isdir(os.path.join(path, item))) for item in contents]
        
        folder_count = 0
        file_count = 0
        
        for item, is_folder in all_items:
            if is_folder:
                if folder_count >= max_folder_each_folder:
                    continue
                folder_count += 1
                try:
                    folder_empty = len(os.listdir(os.path.join(path, item))) == 0
                except (PermissionError, OSError):
                    folder_empty = False  # Assume non-empty if we can't access it
                
                items.append(item + "/" + ('...' if depth == max_depth and not folder_empty else ''))
                items.extend([" " * 4 + subitem for subitem in tree(os.path.join(path, item), depth + 1)])
            else:
                if file_count >= max_file_each_folder:
                    continue
                file_count += 1
                items.append(item)
        
        # Add summary messages for truncated items
        if folder_count == max_folder_each_folder and sum(1 for _, is_folder in all_items if is_folder) > max_folder_each_folder:
            items.append(f"... ({sum(1 for _, is_folder in all_items if is_folder) - max_folder_each_folder} more folders)")
        if file_count == max_file_each_folder and sum(1 for _, is_folder in all_items if not is_folder) > max_file_each_folder:
            items.append(f"... ({sum(1 for _, is_folder in all_items if not is_folder) - max_file_each_folder} more files)")

        return items
    
    path = Path(root_path).expanduser().absolute().as_posix()
    result = tree(path, 1)
    formatted_result = f"File tree under {path}:\n"+"\n".join(result)
    logger.info(f'get_file_tree result: {formatted_result}')
    return formatted_result


