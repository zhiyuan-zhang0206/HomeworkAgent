from dotenv import load_dotenv
load_dotenv(override=True)
from agent.logger import configure_default_logger
configure_default_logger()
import argparse
from agent.multi_agent.run import run_task


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run a multi-agent task')
    parser.add_argument('--task', type=str, help='The task prompt to execute', default=None, required=False)
    args = parser.parse_args()
    run_task(args.task)

# Go straight to finish.
# send an email to me saying hello world
# Ask the math agent to solve 1 + 1 = ?, then tell the document agent to write the answer in "D:\Downloads\answer.txt", then tell the math agent to solve x^2 + 2x + 1 = 0, then send email to me to say hello.
# finish with a message telling me what 1 + 1 = ?
# Call the math agent to solve 1 + 1 = ?
# Call the math agent to solve 1 + 1 = ?, then write the answer in "D:\Downloads\answer.txt"
# Call the math agent to solve 1 + 1 = ?, tell it to read the answer in "D:\Downloads\answer.txt" to see if it's correct, if wrong, write the correct answer in it.
# and I am testing the error handling of tool calls. Tell the math agent to call write file tool in H:\test.txt, but in a wrong way of using the tool.
# email me about the weather in LA
# check which homework I haven't finished on bruinlearn.ucla.edu/courses
# download the latest homework from bruinlearn.ucla.edu/courses
# after completing my homework, send an email to me to tell me about it
# finish the homework TheoreticalStatistics\homework3_q2.pdf