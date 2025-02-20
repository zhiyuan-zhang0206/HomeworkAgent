import os
from pathlib import Path
from typing import Literal, Optional
from langchain_core.tools import tool
from loguru import logger
import mimetypes

@tool
def read_file(filepath: str, 
              line_number: bool = True,
              ) -> str:
    """
    Get the content of a text file (.txt, .py, .md, etc.) after confirming it's a text file.
    
    Args:
        filepath: str
            The path of the file to view.
        line_number: bool
            Whether to show the line number. Default is True.
    """
    path = Path(filepath).expanduser().absolute()
    logger.info(f"Trying to read file: {path.as_posix()}")
    
    if not path.exists():
        return f"File not found: {path.as_posix()}"
    if path.is_dir():
        return f"File is a directory: {path.as_posix()}"

    if not is_text_file(filepath):
        return f"File is not a pure text file: {path.as_posix()}"

    with open(path, 'r', encoding="utf-8") as file:
        lines = file.readlines()
        if line_number:
            num_digits = len(str(len(lines)))
            content = ''.join([f'{idx+1:{num_digits}d}: {line}' for idx, line in enumerate(lines)])
        else:
            content = ''.join(lines)
    logger.info(f'File read successfully: "{path.as_posix()}", content: {content}')
    return content

@tool
def write_file(filepath: str, 
               content: str, 
               mode: Literal["w", "a"] = "w", 
               ) -> str:
    """
    Write the content to the file. Returns the message indicating the success of the operation.

    Args:
        filepath: str
            The path of the file to write.
        content: str
            The content to write to the file.
        mode: Literal["w", "a"]
            The mode to write the file in. "w", overwrite. "a", append.
    """
    original_filepath_string = filepath
    filepath = Path(filepath).expanduser().absolute()
    logger.info(f"Trying to write file: {filepath.as_posix()}, original filepath: {original_filepath_string}")
    if filepath.is_dir():
        return f"File is a directory: {filepath}"
    if not filepath.parent.exists():
        filepath.parent.mkdir(parents=True, exist_ok=True)
    if mode == "a" and not is_text_file(filepath):
        return f"File is not a pure text file: {filepath}"
    if mode == "w" and filepath.exists():
        overwritten = True
    else:
        overwritten = False
    with open(filepath, mode, encoding="utf-8") as file:
        file.write(content)
    logger.info(f'File written (overwritten: {overwritten}) successfully: "{filepath}" with content: {content}')
    if overwritten:
        return f'File overwritten successfully: "{filepath}"'
    else:
        return f'File written successfully: "{filepath}"'

@tool
def edit(filepath, target_platform: Literal["Windows", "Linux"], edit_range, content):
    """
    Edit the file. TODO: implement this.
    Args:
        filepath: str
            The path of the file to edit.
        target_platform: Literal["Windows", "Linux"]
            The platform to edit the file for.
        edit_range: tuple[int, int]
            The start and end line numbers to edit. Start is inclusive, end is exclusive. If start
        content: str
            The content to edit.
    Returns:
        str
            The message indicating the success of the operation.
    """
    pass

@tool
def rename_file(filepath: str, new_name: str):
    """
    Rename the file.

    Args:
        filepath: str
            The path of the file to rename.
        new_name: str
            The new name of the file (with extension).
    """
    filepath = Path(filepath).expanduser().absolute().as_posix()
    logger.info(f"Trying to rename file: {filepath} to {new_name}")
    os.rename(filepath, new_name)
    logger.info(f"File renamed successfully: {filepath} to {new_name}")
    return f"File renamed successfully: {filepath} to {new_name}"

def search_file_by_name(directory, keyword, limit=10, case_sensitive=False):
    """

    Search the file by name.
    Args:
        directory: str
            The directory to search.
        target_platform: Literal["Windows", "Linux"]
            The platform to search the file for.
        keyword: str
            The keyword to search.
        limit: int
            The maximum number of files to return. Default is -1 (no limit).
        case_sensitive: bool
            Whether to match the case of the keyword. Default is False.
        ignore_keywords: list[str]
            The keywords to ignore. Default is DEFAULT_IGNORE_KEYWORDS.
    Returns:
        dict
            The search result. With a "status" and "results" key.
    """
    results = []
    status = "success"
    if not os.path.exists(directory):
        status = "directory not found"
    else:
        for root, dirs, files in os.walk(directory):
            for file in files:
                path = os.path.join(root, file)
                found = keyword in file if case_sensitive else keyword.lower() in file.lower()
                if found:
                    results.append(path)
                if limit > 0 and len(results) >= limit:
                    status = f"hit limit of {limit} results"
                    break
    return {"info": status, 
            "results": results}

def search_file_by_content(directory, keyword, limit=-1, neighbor_lines=3, case_sensitive=False):
    """
    Search the file by content.
    Args:

        directory: str
            The directory to search.
        target_platform: Literal["Windows", "Linux"]
            The platform to search the file for.
        keyword: str
            The keyword to search.
        limit: int
            The maximum number of files to return. Default is -1 (no limit).
        neighbor_lines: int
            The number of lines to include before and after the keyword. Default is 2.
        case_sensitive: bool
            Whether to match the case of the keyword. Default is False.
        ignore_keywords: list[str]
            The keywords to ignore. Default is DEFAULT_IGNORE_KEYWORDS.
    Returns:
        dict
            The search result. With a "status" and "results" key. "results" is a list of dicts, each representing a result, with line number, line content, and line with neighbors.
    """
    results = []

    result_count = 0
    status = "success"
    if not os.path.exists(directory):
        status = "directory not found"
    else:
        for root, dirs, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                content = read_file(filepath)
                found = keyword in content if case_sensitive else keyword.lower() in content.lower()
                if found:
                    result = {
                        "filepath": filepath,
                        "results": []
                    }
                    results.append(result)
                    # find the line numbers, include some neighboring lines
                    lines = content.split("\n")
                    for idx, line in enumerate(lines):
                        found = keyword in line if case_sensitive else keyword.lower() in line.lower()
                        if found:
                            result_count += 1
                            neighbor_start = max(0, idx-neighbor_lines)
                            neighbor_end = min(len(lines), idx+neighbor_lines+1)
                            line_with_neighbors = '\n'.join(lines[neighbor_start:neighbor_end])
                            result["results"].append({'line_number': idx, 'line': line, 'line_with_neighbors': line_with_neighbors})
                            if limit > 0 and result_count >= limit:
                                status = f"hit limit of {limit} results"
                                break
    return {"info": status, 
            "results": results}

def is_text_file(filepath: str, blocksize: int = 1024) -> bool:
    path = Path(filepath)
    # First check using the file's MIME type (based on extension)
    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type is not None:
        if mime_type.startswith('text'):
            return True
        else:
            # For example, PDFs will have "application/pdf"
            return False

    # Fallback: use a heuristic by examining the file content
    try:
        with open(path, 'rb') as file:
            sample = file.read(blocksize)
            # If null bytes are present, it's likely binary.
            if b'\0' in sample:
                return False
            # Try decoding as UTF-8. If it fails, likely binary.
            try:
                sample.decode('utf-8')
            except UnicodeDecodeError:
                return False
            return True
    except Exception:
        # If unable to open / read, assume it's not a text file.
        return False


