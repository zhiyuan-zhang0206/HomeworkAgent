from ..tools.communication import send_email, send_email_to_user
from ..tools.files import write_file, read_file
from .member_agent import make_member_node


COMMUNICATION_ROLE_PROMPT = """
You will act as a communication agent. You can send emails to other people.
You will receive a prompt containing the message to send, and you need to send it to the right recipient.
"""

COMMUNICATION_AGENT_NAME = "communication_agent"

COMMUNICATION_AGENT_ABILITIES = "communication_agent can communicate with the user conveniently, send emails, and read and write pure text files."

communication_node = make_member_node(COMMUNICATION_AGENT_NAME, COMMUNICATION_ROLE_PROMPT, [send_email, send_email_to_user, write_file, read_file])