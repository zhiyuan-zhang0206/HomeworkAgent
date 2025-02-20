
from agent.tools.terminals import open_terminal, command_terminal, get_terminal_output, close_terminal

if __name__ == "__main__":
    print(open_terminal.invoke({"name": "test"}))
    print(command_terminal.invoke({"command": "dir", "name": "test"}))
    print(command_terminal.invoke({"command": "echo hello", "name": "test"}))
    print(get_terminal_output.invoke({"name": "test"}))
    print(close_terminal.invoke({"name": "test"}))

