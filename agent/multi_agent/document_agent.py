from ..tools.pdf2md import convert_pdf2md
from ..tools.files import read_file, write_file, rename_file, get_file_tree
from .member_agent import make_member_node

DOCUMENT_ROLE_PROMPT = """
You will act as a document agent, and you will assist the supervisor agent. You can read, write, and convert documents.
You will receive a request from the supervisor agent, and you will use tools to help.
When converting a non-pure text file to a pure text file, you should save the file to disk, and give a brief summary of the file content, and the file path.
Don't include large texts in your response.
"""

DOCUMENT_AGENT_NAME = "document_agent"

DOCUMENT_AGENT_ABILITIES = "document_agent can access user's file system, read, write pure text files, and convert pdf files to .md files."

document_node = make_member_node(DOCUMENT_AGENT_NAME, 
                                 DOCUMENT_ROLE_PROMPT, 
                                 [read_file, 
                                  convert_pdf2md, 
                                  write_file, 
                                  rename_file, 
                                  get_file_tree])