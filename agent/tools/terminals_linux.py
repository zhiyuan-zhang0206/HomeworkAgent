import atexit
import subprocess
import time
from loguru import logger
from typing import Dict, Optional

class TerminalManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.terminals = {}
            cls._instance.id_to_name = {}
            cls._instance.next_id = 0
            atexit.register(cls._instance._close_all_terminals)
        return cls._instance

    def __init__(self):
        self.terminals: dict[str, str] = getattr(self, 'terminals', {})
        self.id_to_name: dict[int, str] = getattr(self, 'id_to_name', {})
        self.next_id: int = getattr(self, 'next_id', 0)

    def _get_terminal_name(self, id: Optional[int] = None, name: Optional[str] = None) -> Optional[str]:
        if id is not None and id in self.id_to_name:
            return self.id_to_name[id]
        if name is not None and name in self.terminals:
            return name
        return None

    def open(self, name: Optional[str] = None) -> str:
        logger.info(f"Trying to open terminal with {name=}.")
        terminal_id = self.next_id
        
        if name is not None and name in self.terminals:
            return f"Terminal name '{name}' already exists"
        
        actual_name = name if name is not None else f"terminal_{terminal_id}"
        logger.info(f"Opening terminal '{actual_name}' with id {terminal_id}")
        
        try:
            subprocess.run(['tmux', 'new-session', '-d', '-s', actual_name], check=True)
            self.terminals[actual_name] = actual_name
            self.id_to_name[terminal_id] = actual_name
            self.next_id += 1
            message = f"Terminal '{actual_name}' (id={terminal_id}) opened"
            logger.info(message)
            return message
        except subprocess.CalledProcessError:
            message = f"Failed to open terminal '{actual_name}'"
            logger.info(message)
            return message

    def send(self, id: Optional[int] = None, name: Optional[str] = None, command: str = "") -> str:
        logger.info(f"Trying to send command '{command}' to terminal with {id=} and {name=}.")
        if id is None and name is None:
            message = "Provided id and name are both None. Must provide either id or name"
            logger.info(message)
            return message
            
        terminal_name = self._get_terminal_name(id, name)
        if id is not None and terminal_name is None:
            message = f"Terminal (id={id}) not found"
            logger.info(message)
            return message
        elif name is not None and terminal_name is None:
            message = f"Terminal (name={name}) not found"
            logger.info(message)
            return message
        
        logger.info(f"Sending command '{command}' to terminal '{terminal_name}'")
        try:
            if command == "SIGINT":
                subprocess.run(['tmux', 'send-keys', '-t', terminal_name, 'C-c'], check=True)
            else:
                subprocess.run(['tmux', 'send-keys', '-t', terminal_name, command, 'Enter'], check=True)
            return f"Command '{command}' sent to terminal '{terminal_name}'"
        except subprocess.CalledProcessError:
            return f"Failed to send command to terminal '{terminal_name}'"

    def get_output(self, id: Optional[int] = None, name: Optional[str] = None, last_n_lines: Optional[int] = None) -> str:
        logger.info(f"Trying to get output from terminal with {id=} and {name=}.")
        if id is None and name is None:
            message = "Provided id and name are both None. Must provide either id or name"
            logger.info(message)
            return message
            
        terminal_name = self._get_terminal_name(id, name)
        if id is not None and terminal_name is None:
            message = f"Terminal (id={id}) not found"
            logger.info(message)
            return message
        elif name is not None and terminal_name is None:
            message = f"Terminal (name={name}) not found"
            logger.info(message)
            return message
        
        try:
            output = subprocess.check_output(['tmux', 'capture-pane', '-p', '-t', terminal_name]).decode('utf-8').strip()
            output_lines = output.splitlines()
            if last_n_lines is not None:
                output_lines = output_lines[-last_n_lines:]
            output_lines = '\n'.join(output_lines)
            
            logger.info(f"Got output from terminal '{terminal_name}' with {last_n_lines=}.")
            return output_lines
        except subprocess.CalledProcessError:
            return f"Failed to get output from terminal '{terminal_name}'."

    def close(self, id: Optional[int] = None, name: Optional[str] = None) -> str:
        logger.info(f"Trying to close terminal with {id=} and {name=}.")
        if id is None and name is None:
            message = "Provided id and name are both None. Must provide either id or name"
            logger.info(message)
            return message
            
        terminal_name = self._get_terminal_name(id, name)
        if id is not None and terminal_name is None:
            message = f"Terminal (id={id}) not found"
            logger.info(message)
            return message
        elif name is not None and terminal_name is None:
            message = f"Terminal (name={name}) not found"
            logger.info(message)
            return message
        
        logger.info(f"Closing terminal '{terminal_name}'")
        try:
            subprocess.run(['tmux', 'kill-session', '-t', terminal_name], check=True)
            # Find and remove the ID
            terminal_id = next(tid for tid, tname in self.id_to_name.items() if tname == terminal_name)
            del self.id_to_name[terminal_id]
            del self.terminals[terminal_name]
            message = f"Terminal '{terminal_name}' (id={terminal_id}) closed."
            logger.info(message)
            return message
        except subprocess.CalledProcessError:
            message = f"Failed to close terminal '{terminal_name}'."
            logger.info(message)
            return message

    def rename(self, new_name: str, id: Optional[int] = None, name: Optional[str] = None) -> str:
        logger.info(f"Trying to rename terminal with {id=} and {name=} to '{new_name}'.")
        if id is None and name is None:
            message = "Provided id and name are both None. Must provide either id or name"
            logger.info(message)
            return message
            
        terminal_name = self._get_terminal_name(id, name)
        if id is not None and terminal_name is None:
            message = f"Terminal (id={id}) not found"
            logger.info(message)
            return message
        elif name is not None and terminal_name is None:
            message = f"Terminal (name={name}) not found"
            logger.info(message)
            return message
        
        if new_name in self.terminals:
            message = f"Terminal name '{new_name}' already exists"
            logger.info(message)
            return message
        
        try:
            subprocess.run(['tmux', 'rename-session', '-t', terminal_name, new_name], check=True)
            # Update the mappings
            terminal_id = next(tid for tid, tname in self.id_to_name.items() if tname == terminal_name)
            self.id_to_name[terminal_id] = new_name
            self.terminals[new_name] = new_name
            del self.terminals[terminal_name]
            message = f"Terminal '{terminal_name}' (id={terminal_id}) renamed to '{new_name}'."
            logger.info(message)
            return message
        except subprocess.CalledProcessError:
            message = f"Failed to rename terminal '{terminal_name}'"
            logger.info(message)
            return message

    def list_all(self) -> Dict[int, str]:
        terminal_dict = {id: name for id, name in self.id_to_name.items()}
        logger.info(f"Listing terminals: {terminal_dict}")
        return terminal_dict

    def _close_all_terminals(self):
        keys = list(self.terminals.keys())
        for terminal_name in keys:
            self.close(name=terminal_name)
        logger.info(f"Closed all terminals: {keys}")

def open_terminal(name: Optional[str] = None) -> str:
    '''
    Open a new terminal. Returns a message indicating the success or failure of the operation.
    Cannot have duplicate names.

    Args:
        name (optional): The name of the terminal. If not provided, a default name is used.
    '''
    terminal_manager = TerminalManager()
    return terminal_manager.open(name)

def command_terminal(command: str, id: Optional[int] = None, name: Optional[str] = None) -> str:
    '''
    Send a command to a terminal.
    Args:
        command: The command to send to the terminal.
        id (optional): The id of the terminal.
        name (optional): The name of the terminal.
    Returns:
        A message indicating the success or failure of the operation.
    Must provide either id or name.
    To Ctrl+C, use command="SIGINT".
    '''
    terminal_manager = TerminalManager()
    return terminal_manager.send(id=id, name=name, command=command)

def get_terminal_output(id: Optional[int] = None, name: Optional[str] = None, lines: Optional[int] = None) -> str:
    '''
    Get the output of a terminal.
    Args:
        id (optional): The id of the terminal.
        name (optional): The name of the terminal.
        lines (optional): The number of lines to get from the output.
    Returns:
        The output of the terminal.
    Must provide either id or name.
    '''
    time.sleep(1)
    terminal_manager = TerminalManager()
    return terminal_manager.get_output(id=id, name=name, last_n_lines=lines)

def close_terminal(id: Optional[int] = None, name: Optional[str] = None) -> str:
    '''
    Close a terminal.
    Args:
        id (optional): The id of the terminal.
        name (optional): The name of the terminal.
    Returns:
        A message indicating the success or failure of the operation.
    Must provide either id or name.
    '''
    terminal_manager = TerminalManager()
    return terminal_manager.close(id=id, name=name)

def rename(new_name: str, id: Optional[int] = None, name: Optional[str] = None) -> str:
    '''
    Rename a terminal.
    Args:
        new_name: The new name of the terminal.
        id (optional): The id of the terminal.
        name (optional): The name of the terminal.
    Returns:
        A message indicating the success or failure of the operation.
    Must provide either id or name.
    '''
    terminal_manager = TerminalManager()
    return terminal_manager.rename(new_name=new_name, id=id, name=name)

def list_all() -> Dict[int, str]:
    '''
    List all terminals.
    Returns:
        A dictionary of the terminals with their ids.
    '''
    terminal_manager = TerminalManager()
    return terminal_manager.list_all()


__all__ = ['open_terminal', 'command_terminal', 'get_terminal_output', 'close_terminal', 'rename', 'list_all', 'help']