from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
from loguru import logger

from .state import State
from .supervisor_agent import supervisor_node, SUPERVISOR_AGENT_NAME, supervisor_human_node, SUPERVISOR_HUMAN_NODE_NAME
from .coder_agent import coder_node, CODER_AGENT_NAME
from .math_agent import math_node, MATH_AGENT_NAME
from .communication_agent import communication_node, COMMUNICATION_AGENT_NAME
from .browser_agent import browser_node, BROWSER_AGENT_NAME
from .document_agent import document_node, DOCUMENT_AGENT_NAME

MEMBER_NODES = {
    CODER_AGENT_NAME: coder_node,
    MATH_AGENT_NAME: math_node,
    BROWSER_AGENT_NAME: browser_node,
    COMMUNICATION_AGENT_NAME: communication_node,
    DOCUMENT_AGENT_NAME: document_node,
}

def get_graph():
    builder = StateGraph(State) # TODO: input=InputState, output=OutputState
    builder.add_node(SUPERVISOR_AGENT_NAME, supervisor_node)
    builder.add_node(SUPERVISOR_HUMAN_NODE_NAME, supervisor_human_node) # TODO: wrap this node in supervisor_agent, or human_node?
    for name, node in MEMBER_NODES.items():
        builder.add_node(name, node)
    builder.set_entry_point(SUPERVISOR_AGENT_NAME)
    graph = builder.compile()
    return graph

def run_task(task_prompt: str = None):
    if task_prompt is None:
        task_prompt = input("Enter the task prompt: ")
    logger.info(f"Running task: {task_prompt}")
    graph = get_graph()
    stream = graph.stream(input={"supervisor_messages": [HumanMessage(content=f"{task_prompt}")]},
                          config={"recursion_limit": 100})
    for event in stream:
        pass