from typing import Literal
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import Command
from loguru import logger
from .math_agent import MATH_AGENT_ABILITIES, MATH_AGENT_NAME
from .coder_agent import CODER_AGENT_ABILITIES, CODER_AGENT_NAME
from .communication_agent import COMMUNICATION_AGENT_ABILITIES, COMMUNICATION_AGENT_NAME
from .document_agent import DOCUMENT_AGENT_ABILITIES, DOCUMENT_AGENT_NAME
from .browser_agent import BROWSER_AGENT_ABILITIES, BROWSER_AGENT_NAME
from .supervisor_agent_name import SUPERVISOR_AGENT_NAME
from ..llms import SUPERVISOR_MODEL
from .state import State
from .get_relevant_memories import get_relevant_memories
from ..llm_calling import get_and_parse_json_response
from ..timestamp import get_current_timestamp
from .memory_updater import update_memories

SUPERVISOR_HUMAN_NODE_NAME = "supervisor_human_node"

MEMBER_AGENT_NAMES = [
    MATH_AGENT_NAME,
    CODER_AGENT_NAME,
    COMMUNICATION_AGENT_NAME,
    DOCUMENT_AGENT_NAME,
    BROWSER_AGENT_NAME,
]

AGENT_ABILITIES = {
    MATH_AGENT_NAME: MATH_AGENT_ABILITIES,
    CODER_AGENT_NAME: CODER_AGENT_ABILITIES,
    COMMUNICATION_AGENT_NAME: COMMUNICATION_AGENT_ABILITIES,
    DOCUMENT_AGENT_NAME: DOCUMENT_AGENT_ABILITIES,
    BROWSER_AGENT_NAME: BROWSER_AGENT_ABILITIES,
}

SUPERVISOR_PROMPT = f"""
You are an AI agent. You are designed to serve your only user.

Response format:
Respond in JSON. Don't include "```json" nor "```" in your response.
You should respond a JSON object with the following fields:
- "thoughts": your thoughts about the task
- "next_agent": the name of the next agent to call
- "next_agent_prompt": the prompt for the next agent

Example 1:
{{
    "thoughts": "The user asked me to ... I need to let math_agent solve the math problems in the file D:/math/questions.md.",
    "next_agent": "math_agent",
    "next_agent_prompt": "Read the file D:/math/questions.md and solve the math problems."
}}

Example 2:
{{
    "thoughts": "The math problems are solved and saved in file D:/report.md.",
    "next_agent": "__end__",
    "next_agent_prompt": "The math problems are solved and saved in file D:/report.md."
}}

Your responsibilities and strategies:
You will act as a supervisor agent. You can give tasks to other agents, and they report back to you. Don't do anything that they can do.
Agent names and abilities are as follows:
{"\n".join([f"{name}: {abilities}" for name, abilities in AGENT_ABILITIES.items()])}

They will report back to you with a brief summary of their actions and results. You should always try to verify their results.
When giving a task to an agent, you should provide clear and specific instructions in the `next_agent_prompt` field.
Remember that member agents are not newly spawned each time they are called. They maintain their own conversation history and context across interactions.
Try to avoid repeating the information to other agents, when you can pass the information source (file paths, etc.) to the agent.
Put "__end__" in next_agent and an empty string in next_agent_prompt means you are done, and no more agent calls are needed.

Each step, the system will examine your long-term memories. If there are some helpful memories, it will provide them to you after the string "Relevant long-term memories:". You can use the memories to help you make decisions.

If you need more information or to make a decision, you can let the communication agent send a message to the user.
"""

def supervisor_node(state: State) -> Command[Literal[SUPERVISOR_AGENT_NAME, *MEMBER_AGENT_NAMES, "__end__"]]: # type: ignore
    logger.info("Entering supervisor node.")
    messages = state['supervisor_messages']
    if len(messages) == 1: # if just started, add system message
        if hasattr(messages[-1], "content"):
            content = messages[-1].content
        else:
            content = messages[-1]['content']
        input_prompt = f'System message: \nCurrent time: {get_current_timestamp()}\nUser gave you a task: {content}'
        logger.info(f"Input prompt: {input_prompt}")
        messages = [SystemMessage(content=SUPERVISOR_PROMPT), HumanMessage(content=input_prompt)]
    if state.get("member_finish_message", None): # if a member agent finished, add a message
        messages.append(HumanMessage(content=f'Agent {state["next_agent"]} sent a message: {state["member_finish_message"]}'))
    if state.get("from_human_interrupt", False):
        messages[-1].content = messages[-1].content + f'\n\nHuman instruction message: {state["human_instruction_message"]}'
    _, memory_ids, memory_formatted = get_relevant_memories(messages, 
                                                            exclude_ids=state.get("supervisor_retrieved_memory_ids", []))
    messages[-1].content = messages[-1].content + memory_formatted
    response, parsed_response = get_and_parse_json_response(SUPERVISOR_MODEL, messages)
    messages.append(AIMessage(content=response, name=SUPERVISOR_AGENT_NAME))
    next_agent = parsed_response["next_agent"]
    
    return Command(goto=SUPERVISOR_HUMAN_NODE_NAME, update={
                                    "supervisor_messages": messages,
                                    "supervisor_retrieved_memory_ids": state.get("supervisor_retrieved_memory_ids", []) + memory_ids,
                                    "next_agent": next_agent,
                                    "next_agent_prompt": parsed_response["next_agent_prompt"]
                                    })



def supervisor_human_node(state: State) -> Command[Literal[SUPERVISOR_AGENT_NAME, *MEMBER_AGENT_NAMES, "__end__"]]: # type: ignore
    value = input("Input your instruction here. Leave blank if you don't have any:\nInstruction: ").strip()
    if value:
        logger.info(f"Human instruction: {value}")
        messages = state['supervisor_messages']
        messages.append(HumanMessage(content=f'System: human interrupted with instruction message: {value}'))
        return Command(goto=SUPERVISOR_AGENT_NAME, update={
            "supervisor_messages": messages
        })
    else:
        logger.info(f"No human instruction, routing to {state['next_agent']}.")
        if state["next_agent"] == "__end__":
            update_memories(state)
            return Command(goto="__end__")
        else:
            return Command(goto=state["next_agent"])