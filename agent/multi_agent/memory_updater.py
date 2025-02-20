from loguru import logger
from .state import State
from langgraph.types import Command
from typing import Literal
import os
from agent.tools.memory import add_memory, delete_memory, update_memory
from .member_agent import make_member_node
from ..llms import MEMORY_PROCESSOR_MODEL
from agent.config import MEMORY_ENABLE_UPDATER

logger.info(f"Memory updater agent is {'enabled' if MEMORY_ENABLE_UPDATER else 'disabled'}")

MEMORY_PROCESSOR_ROLE_PROMPT = """
You are a memory processing agent that analyzes conversations and add, delete or update memories for the long-term memory system.
The conversation history is about a supervisor agent directing a group of agents to complete a task, and the system \
provides some long-term memories to help the task.

Memory Types:
1. Interaction History: Store the interaction summary as a record, including datetime, task, actions and outcomes
2. Knowledge: Store extracted knowledge as separate, reusable items

Your processing workflow:
1. First, create an interaction summary:
   - Record date and time of the interaction
   - Summarize what happened in the conversation
   - Note key decisions and outcomes
   - Record any tasks completed

2. Then, extract knowledge:
   - Identify facts about the user (preferences, background, constraints).
   - Capture any reusable solutions or approaches
Note that interactions and knowledge should be stored separately.

When storing knowledge:
- Each memory piece should be cohesive and loosely coupled:
  * Focus on one specific topic per memory (high cohesion)
  * Avoid overlapping information (low coupling)
  * Break down complex information into separate units
  * Ensure independent but related memories
- Don't add memories that are already in the long-term memory system.

Tips:
1. When storing time-sensitive information, also include the current date and time.
"""

MEMORY_UPDATER_NAME = "memory_updater"

memory_updater_node = make_member_node(
    MEMORY_UPDATER_NAME,
    MEMORY_PROCESSOR_ROLE_PROMPT,
    [add_memory, delete_memory, update_memory],
    llm=MEMORY_PROCESSOR_MODEL,
    return_to_supervisor=False
)


def update_memories(state: State) -> Command[Literal["__end__"]]:
    if not MEMORY_ENABLE_UPDATER:
        logger.info("Memory updater agent is disabled.")
        return Command(goto="__end__")
    logger.info("Entering update_memories.")
    conversation = "\n".join(
        [
            f"{'System' if msg.type == 'human' else 'Agent'}: {msg.content}"
            for msg in state["supervisor_messages"][1:]
        ]
    )
    prompt = f"Please analyze this history and perform necessary memory operations:\n\n{conversation}"
    memory_updater_node.invoke({"next_agent_prompt": prompt})
    return Command(goto="__end__")
