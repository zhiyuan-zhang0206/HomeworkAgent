from ..tools.files import read_file, write_file
from ..tools.terminals import open_terminal, command_terminal, get_terminal_output, close_terminal
from .member_agent import make_member_node


CODER_ROLE_PROMPT = """
You will act as a coder agent.
You can read and write files, open and close terminals, and get the output of a terminal.
"""

CODER_AGENT_NAME = "coder_agent"

CODER_AGENT_ABILITIES = "coder_agent can do some coding tasks. It can read and write pure text files, open and close terminals, and get the output of a terminal."


coder_node = make_member_node(CODER_AGENT_NAME, 
                              CODER_ROLE_PROMPT, 
                              [read_file, 
                               write_file, 
                               open_terminal, 
                               command_terminal, 
                               get_terminal_output, 
                               close_terminal])