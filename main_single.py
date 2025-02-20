from agent.tools.files import read_file, write_file
from agent.tools.terminals import open_terminal, command_terminal, get_terminal_output, close_terminal
from agent.multi_agent.member_agent import make_member_node
from agent.logger import configure_default_logger
from dotenv import load_dotenv
configure_default_logger()
load_dotenv()

CODER_ROLE_PROMPT = """
You will act as a coder agent.
You can read and write files, open and close terminals, and get the output of a terminal.
"""

CODER_AGENT_NAME = "coder_agent"

CODER_AGENT_ABILITIES = "coder_agent can do some coding tasks. It can read and write pure text files, open and close terminals, and get the output of a terminal."


if __name__ == "__main__":
    coder_node = make_member_node(CODER_AGENT_NAME, 
                                CODER_ROLE_PROMPT, 
                                [read_file, 
                                write_file, 
                                open_terminal, 
                                command_terminal, 
                                get_terminal_output, 
                                close_terminal],
                                return_to_supervisor=False)
    coder_node.invoke(
        {"next_agent_prompt": r"use python to calculate the 33th term of the Fibonacci sequence"}
    )