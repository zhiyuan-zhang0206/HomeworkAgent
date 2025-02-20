from ..tools.files import write_file, read_file, get_file_tree
from .member_agent import make_member_node
from ..llms import MATH_AGENT_MODEL

MATH_ROLE_PROMPT = """
You will act as a math agent.
You will receive some instructions about math problems from a supervisor agent, and you need to solve them.
In your solution, you need to:
1. Get the math problems, whether from the user or from a file.
2. Organize the solutions into a complete solution.
3. Use .md format and syntax. Note that for math expressions, you should always single use dollar quote "$...$" for inline math expressions or symbols and double dollar quote "$$...$$" for block math expressions.
4. If there are coding needed, you should skip it and tell the supervisor about it.
5. If the detailed solutions are very long, you should write the detailed solutions to a file and give the file path to the supervisor. Avoid putting too much information in the summary message.
6. If there are multiple math problems, you should solve them one by one and give the solution of each problem one by one. Don't rush to give all the solutions at once.
"""

MATH_AGENT_NAME = "math_agent"

MATH_AGENT_ABILITIES = "math_agent can solve math problems. It can read and write pure text files."

math_node = make_member_node(MATH_AGENT_NAME, MATH_ROLE_PROMPT, 
                             [read_file, 
                              write_file,
                              get_file_tree], 
                             llm=MATH_AGENT_MODEL)

