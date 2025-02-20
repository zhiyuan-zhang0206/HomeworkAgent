import atexit
from langchain_core.tools import tool
import os
import subprocess
import time
import signal
import threading
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
        self.terminals: Dict[str, dict] = getattr(self, 'terminals', {})
        self.id_to_name: Dict[int, str] = getattr(self, 'id_to_name', {})
        self.next_id: int = getattr(self, 'next_id', 0)

    def _get_terminal_name(self, id: Optional[int] = None, name: Optional[str] = None) -> Optional[str]:
        if id is not None and id in self.id_to_name:
            return self.id_to_name[id]
        if name is not None and name in self.terminals:
            return name
        return None

    def _reader(self, pipe, buffer):
        while True:
            line = pipe.readline()
            if not line:
                break
            buffer.append(line)
        pipe.close()

    def open(self, name: Optional[str] = None) -> str:
        logger.info(f"Trying to open terminal with {name=}.")
        terminal_id = self.next_id
        
        if name is not None and name in self.terminals:
            return f"Terminal name '{name}' already exists"
        
        actual_name = name if name is not None else f"terminal_{terminal_id}"
        logger.info(f"Opening terminal '{actual_name}' with id {terminal_id}")
        
        try:
            logger.info("Opening powershell.exe")
            proc = subprocess.Popen(
                ['powershell.exe'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                env=os.environ.copy()
            )
            
            stdout_buffer = []
            reader_thread = threading.Thread(
                target=self._reader, args=(proc.stdout, stdout_buffer)
            )
            reader_thread.daemon = True
            reader_thread.start()

            self.terminals[actual_name] = {
                'process': proc,
                'stdout_buffer': stdout_buffer,
                'id': terminal_id
            }
            self.id_to_name[terminal_id] = actual_name
            self.next_id += 1

            # Wait for PowerShell startup message
            start_time = time.time()
            timeout = 30  # 10 second timeout
            while time.time() - start_time < timeout:
                output = self.get_output(name=actual_name)
                if "Windows PowerShell\nCopyright (C) Microsoft Corporation. All rights reserved.\n\nInstall the latest PowerShell for new features and improvements! https://aka.ms/PSWindows\n\nLoading personal and system profiles took" in output:
                    time_taken = time.time() - start_time
                    logger.info(f"Waited {time_taken:.4f} seconds for PowerShell to start")
                    time.sleep(0.1)
                    break
                time.sleep(0.1)

            message = f"Terminal '{actual_name}' (id={terminal_id}) opened"
            logger.info(message)
            return message
        except Exception as e:
            message = f"Failed to open terminal '{actual_name}': {str(e)}"
            logger.error(message)
            return message

    def send(self, id: Optional[int] = None, name: Optional[str] = None, command: str = "") -> str:
        logger.info(f"Trying to send command '{command}' to terminal with {id=} and {name=}.")
        terminal_name = self._get_terminal_name(id, name)

        if terminal_name is None:
            msg = f"Terminal {'id='+str(id) if id else 'name='+name} not found"
            logger.warning(msg)
            return msg
        
        terminal = self.terminals.get(terminal_name)
        if not terminal:
            msg = f"Terminal '{terminal_name}' not found"
            logger.warning(msg)
            return msg
        
        proc = terminal['process']
        try:
            if command == "SIGINT":
                proc.send_signal(signal.CTRL_BREAK_EVENT)
                msg = f"Sent SIGINT to terminal '{terminal_name}'"
                logger.info(msg)
                return msg
            else:
                proc.stdin.write(command + '\n')
                proc.stdin.flush()
                msg = f"Command '{command}' sent to terminal '{terminal_name}'"
                logger.info(msg)
                return msg
        except Exception as e:
            msg = f"Failed sending to terminal '{terminal_name}': {str(e)}"
            logger.error(msg)
            return msg

    def get_output(self, id: Optional[int] = None, name: Optional[str] = None, last_n_lines: Optional[int] = None) -> str:
        terminal_name = self._get_terminal_name(id, name)
        if terminal_name is None:
            msg = f"Terminal {'id='+str(id) if id else 'name='+name} not found"
            logger.warning(msg)
            return msg
        
        terminal = self.terminals.get(terminal_name)
        if not terminal:
            return f"Terminal '{terminal_name}' not found"
        
        buffer = terminal['stdout_buffer'].copy()
        if last_n_lines is not None:
            buffer = buffer[-last_n_lines:]
        return ''.join(buffer)

    def close(self, id: Optional[int] = None, name: Optional[str] = None) -> str:
        terminal_name = self._get_terminal_name(id, name)
        if terminal_name is None:
            msg = f"Terminal {'id='+str(id) if id else 'name='+name} not found"
            logger.warning(msg)
            return msg
        
        terminal = self.terminals.get(terminal_name)
        if not terminal:
            return f"Terminal '{terminal_name}' not found"
        
        terminal_id = terminal['id']
        terminal['process'].kill()
        del self.terminals[terminal_name]
        del self.id_to_name[terminal_id]
        msg = f"Closed terminal '{terminal_name}' (id={terminal_id})"
        logger.info(msg)
        return msg

    def rename(self, new_name: str, id: Optional[int] = None, name: Optional[str] = None) -> str:
        terminal_name = self._get_terminal_name(id, name)
        if terminal_name is None:
            return f"Terminal {'id='+str(id) if id else 'name='+name} not found"
        
        if new_name in self.terminals:
            return f"Terminal name '{new_name}' already exists"
        
        terminal = self.terminals[terminal_name]
        terminal_id = terminal['id']
        
        self.terminals[new_name] = terminal
        del self.terminals[terminal_name]
        self.id_to_name[terminal_id] = new_name
        
        return f"Renamed terminal '{terminal_name}' to '{new_name}'"

    def list_all(self) -> Dict[int, str]:
        return dict(self.id_to_name)

    def _close_all_terminals(self):
        for name in list(self.terminals.keys()):
            self.close(name=name)

@tool
def open_terminal(name: str = None) -> str:
    '''
    Open a new terminal. Returns a message indicating the success or failure of the operation.
    Cannot have duplicate names.

    Args:
        name: The name of the terminal. If not provided, a default name is used.
    '''
    terminal_manager = TerminalManager()
    return terminal_manager.open(name)

@tool
def command_terminal(command: str, id: int = None, name: str = None) -> str:
    '''
    Send a command to a terminal.
    Returns a message indicating the success or failure of the operation.
    Must provide either id or name.
    To use Ctrl+C, use command="SIGINT".

    Args:
        command: The command to send to the terminal.
        id: The id of the terminal.
        name: The name of the terminal.
    '''
    terminal_manager = TerminalManager()
    return terminal_manager.send(id=id, name=name, command=command)

@tool
def get_terminal_output(id: int = None, name: str = None, lines: int = None) -> str:
    '''
    Get the output of a terminal.
    Returns the output of the terminal.
    Must provide either id or name.

    Args:
        id: The id of the terminal.
        name: The name of the terminal.
        lines: The number of lines to get from the output.
    '''
    time.sleep(0.5)  # Allow buffer to update
    terminal_manager = TerminalManager()
    return terminal_manager.get_output(id=id, name=name, last_n_lines=lines)

@tool
def close_terminal(id: int = None, name: str = None) -> str:
    '''
    Close a terminal.
    Returns a message indicating the success or failure of the operation.
    Must provide either id or name.

    Args:
        id: The id of the terminal.
        name: The name of the terminal.
    '''    
    terminal_manager = TerminalManager()
    return terminal_manager.close(id=id, name=name)

@tool
def rename_terminal(new_name: str, id: int = None, name: str = None) -> str:
    '''
    Rename a terminal.
    Args:
        new_name: The new name of the terminal.
        id: The id of the terminal.
        name: The name of the terminal.
    Returns:
        A message indicating the success or failure of the operation.
    Must provide either id or name.
    '''
    terminal_manager = TerminalManager()
    return terminal_manager.rename(new_name=new_name, id=id, name=name)

@tool
def list_all_terminals() -> Dict[int, str]:
    '''
    List all terminals.
    Returns:
        A dictionary of the terminals with their ids.
    '''
    terminal_manager = TerminalManager()
    return terminal_manager.list_all()

__all__ = ['open_terminal', 'command_terminal', 'get_terminal_output',
           'close_terminal', 'rename_terminal', 'list_all', 'help']


