from langchain_core.messages import AnyMessage
from typing import TypedDict, Any, Optional
from typing_extensions import Annotated

def replace_reducer(old, new):
    return new

class State(TypedDict):
    supervisor_messages: Annotated[list[AnyMessage], replace_reducer] = []
    supervisor_retrieved_memory_ids: Annotated[list[str], replace_reducer] = []
    supervisor_trigger_long_term_memory: Annotated[bool, replace_reducer] = None
    
    next_agent: Annotated[str, replace_reducer] = None # TODO: must use Annotated, cannot simply replace the state, because langgraph thinks there are concurrent updates to the same key
    next_agent_prompt: Annotated[str, replace_reducer] = None

    member_messages: Annotated[dict[str, list[AnyMessage]], replace_reducer] = {}
    member_tool_calls: Annotated[dict[str, list[dict[str, Any]]], replace_reducer] = {}
    member_finish_message: Annotated[dict[str, str], replace_reducer] = {}
    member_retrieved_memory_ids: Annotated[dict[str, list[str]], replace_reducer] = {}
    member_trigger_long_term_memory: Annotated[dict[str, bool], replace_reducer] = {}

