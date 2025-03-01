import traceback
from typing import Literal
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import Command
from loguru import logger
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph
from .supervisor_agent_name import SUPERVISOR_AGENT_NAME
from ..llms import MEMBER_DEFAULT_MODEL
from .get_relevant_memories import get_relevant_memories
from ..tools.notify_supervisor import notify_supervisor
from ..llm_calling import get_and_parse_json_response
from .memory_trigger_tools import is_trigger_memory_tool
from .state import State
def make_tools_prompt(tools: dict[str, BaseTool]):
    return "Tools specified below:\n" + "\n\n\n".join(
        [f"Tool name: {name}:\n{tool.description}" for name, tool in tools.items()]
    )

MEMBER_PROMPT_TEMPLATE = """
You are an AI agent. You will output your thoughts and tool calls, the system will execute the tool calls and return the results to you.

Response format specified below:
Respond in JSON. Don't include "```json" nor "```" in your response.
You should respond a JSON object with the following fields:
- "thoughts": your thoughts about the task,
- "tool_calls": a list of tool calls you are calling, this should never be empty,
    - "name": the tool name to call,
    - "args": the arguments to pass to the tool.

If you need assistance or clarification use the "notify_supervisor" tool and put your assistant request in the "summary" field.
If you have completed your task, call the "notify_supervisor" tool and put your summary in the "summary" field.
The supervisor agent is responsible for orchestrating the overall task and can provide guidance or delegate sub-tasks if necessary.

Example 1:
{
    "thoughts": "The supervisor told me about ... Now I need to read the file D:/math/questions.md.",
    "tool_calls": [
        {
            "name": "read_file",
            "args": {
                "filepath": "D:/math/questions.md"
            }
        }
    ]
}

Example 2:
{
    "thoughts": "The math problem describes... I should solve it this way... After writing the solution into the file, I will call notify_supervisor.",
    "tool_calls": [
        {
            "name": "write_file",
            "args": {
                "filepath": "D:/report.md",
                "content": "We first consider..."
            }
        }
    ]
}

Example 3:
{
    "thoughts": "Based on the feedback from tools, ... So I should call notify_supervisor as the only tool call.",
    "tool_calls": [
        {
            "name": "notify_supervisor",
            "args": {
                "summary": "I solved the math problems and saved the solutions in file D:/report.md."
            }
        }
    ]
}
"""


def make_member_llm_node(agent_name: str, role_prompt: str, llm = MEMBER_DEFAULT_MODEL, tools: dict[str, BaseTool] = {}):
    def llm_node(state: State) -> Command[Literal[agent_name, "tools"]]:  # type: ignore
        logger.info(f"Entering {agent_name} llm_node.")

        # Initialize agent's message history if it's a new agent call
        if agent_name not in state["member_messages"]:
            system_prompt = (
                MEMBER_PROMPT_TEMPLATE
                + f"\nYour role:\n{role_prompt}\n\n"
                + make_tools_prompt(tools)
            )
            state["member_messages"][agent_name] = [SystemMessage(content=system_prompt)]
            state["member_tool_calls"][agent_name] = []
            state["member_trigger_long_term_memory"][agent_name] = False
            state["member_retrieved_memory_ids"][agent_name] = []

        if state["next_agent_prompt"]:
            prompt = state["next_agent_prompt"]
            logger.info(f"{agent_name} llm_node processing prompt from supervisor: {prompt}")
            state["member_messages"][agent_name].append(HumanMessage(content=f"Supervisor message: {prompt}")) # TODO: use add_message reducer
            state["member_tool_calls"][agent_name] = []
            state["member_trigger_long_term_memory"][agent_name] = True
            state["member_retrieved_memory_ids"][agent_name] = []
            state["next_agent_prompt"] = None
            return Command(update=state, goto=agent_name)

        agent_messages = state["member_messages"][agent_name]

        if state["member_trigger_long_term_memory"].get(agent_name, False): # Use .get() to avoid KeyError if agent_name not in dict
            logger.info(f"{agent_name} retrieving memories")
            retrieved_memory_ids = state["member_retrieved_memory_ids"].get(agent_name, []) # Use .get()
            _, memory_ids, memory_formatted = get_relevant_memories(agent_messages, exclude_ids=retrieved_memory_ids)
            retrieved_memory_ids.extend(memory_ids)
            agent_messages[-1].content = agent_messages[-1].content + memory_formatted
            state["member_retrieved_memory_ids"][agent_name].extend(retrieved_memory_ids)
            state["member_trigger_long_term_memory"][agent_name] = False
            return Command(update=state, goto=agent_name)
        else:
            logger.info(f"{agent_name} no memory trigger tool calls, skipping memory retrieval")

        response, parsed_response = get_and_parse_json_response(llm, agent_messages)
        agent_messages.append(AIMessage(content=response))
        try:
            thoughts, tool_calls = parsed_response["thoughts"], parsed_response["tool_calls"]
        except KeyError:
            logger.warning(f"{agent_name} error parsing JSON response: {parsed_response}")
            agent_messages.append(
                HumanMessage(
                    content="System: reminder: you should include one and only one 'thoughts' and 'tool_calls' field in your response."
                )
            )
            state["member_tool_calls"][agent_name] = []
            state["member_trigger_long_term_memory"][agent_name] = False
            return Command(update=state, goto=agent_name)
        if not tool_calls:
            logger.warning(f"{agent_name} did not return any tool calls; reminding LLM.")
            agent_messages.append(
                HumanMessage(
                    content="System: reminder: you should call at least one tool. If everything is done, call the tool 'notify_supervisor'."
                )
            )
            state["member_tool_calls"][agent_name] = []
            state["member_trigger_long_term_memory"][agent_name] = False
            return Command(update=state, goto=agent_name)
        logger.info(f"{agent_name} llm_node called, going to tools_node")
        state["member_tool_calls"][agent_name] = tool_calls
        state["member_trigger_long_term_memory"][agent_name] = False
        return Command(goto="member_human_node", update=state)
    return llm_node

def make_member_human_node(agent_name: str):
    def human_node(state: State) -> Command[Literal[agent_name, "tools"]]:  # type: ignore
        value = input("Input your instruction here. Leave blank if you don't have any:\nInstruction: ").strip()
        if value:
            logger.info(f"Human instruction: {value}")
            messages = state["member_messages"][agent_name] # TODO: use langchain breakpoint
            messages.append(HumanMessage(content=f'System: None of the tool calls are executed because human interrupted with instruction message: {value}'))
            return Command(goto=agent_name, update=state)
        else:
            logger.info(f"No human instruction, going to tools_node")
            return Command(goto="tools")
    return human_node

def make_member_tools_node(agent_name: str, tools: dict[str, BaseTool], return_to_supervisor: bool = True):
    def tools_node(state: State) -> Command[Literal[agent_name]]:  # type: ignore
        logger.info(f"Entering {agent_name} tools_node.")
        tool_calls = state["member_tool_calls"][agent_name]
        messages = state["member_messages"][agent_name]
        
        if len(tool_calls) == 0:
            logger.warning(f"{agent_name} no tool calls")
            messages.append(
                HumanMessage(
                    content="System: reminder: you should call at least one tool. If everything is done, call the tool 'notify_supervisor'."
                )
            )
            state["member_trigger_long_term_memory"][agent_name] = False
            return Command(goto=agent_name, update=state)
        
        if len(tool_calls) > 1 and any(tool_call["name"] == "notify_supervisor" for tool_call in tool_calls):
            logger.warning(f"{agent_name} called notify_supervisor but there are still tools to call")
            messages.append(
                HumanMessage(
                    content="System: No tool calls are executed. Reminder: \"notify_supervisor\" cannot be used with other tools. It should be the only tool call when you have verified all tool call outputs and decided to stop."
                )
            )
            state["member_trigger_long_term_memory"][agent_name] = False
            return Command(goto=agent_name, update=state)
        
        # Handle notify_supervisor tool call
        if len(tool_calls) == 1 and tool_calls[0]["name"] == "notify_supervisor":
            notify_call = tool_calls[0]
            notify_result = tools["notify_supervisor"].invoke(notify_call["args"])
            logger.info(f"{agent_name} notify_supervisor call: {notify_call} produced result: {notify_result}")
            notify_message = notify_call["args"]["summary"]
            logger.info(f"{agent_name} notify supervisor with message: {notify_message}")
            if return_to_supervisor:
                logger.info(f"{agent_name} returning control to supervisor")
                state["member_finish_message"][agent_name] = notify_message
                state["member_tool_calls"][agent_name] = []
                state["member_trigger_long_term_memory"][agent_name] = False
                return Command(goto=SUPERVISOR_AGENT_NAME, graph=Command.PARENT, update=state)
            else:
                logger.info(f"{agent_name} returning notify message in a dict")
                return {"notify_supervisor_message": notify_message}

        for tool_call in tool_calls:
            if tool_call["name"] not in tools:
                logger.warning(f"{agent_name} unknown tool: {tool_call['name']}")
                messages.append(
                    HumanMessage(
                        content=f"System: None tool calls are executed because tool {tool_call['name']} not found, please try again."
                    )
                )
                state["member_trigger_long_term_memory"][agent_name] = False
                return Command(goto=agent_name, update=state)

        tool_call_results = []
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            try:
                tool_result = tools[tool_name].invoke(tool_call["args"])
            except Exception as e:
                tool_result = f"Error: {e}"
                logger.warning(f"{agent_name} tool call: {tool_call} produced error: {e}. Traceback: {traceback.format_exc()}")
            tool_call_results.append((tool_name, tool_result))
            logger.info(f"{agent_name} tool call: {tool_call} produced result: {tool_result}")
        
        results_message = "\n".join(
            [f'Tool "{name}" result: {result}' for name, result in tool_call_results]
        )
        messages.append(HumanMessage(content=results_message))
        logger.info(f"{agent_name} not finished, going back to llm_node")
        state["member_trigger_long_term_memory"][agent_name] = any(is_trigger_memory_tool(call["name"]) for call in tool_calls)
        state["member_tool_calls"][agent_name] = []
        return Command(update=state, goto=agent_name)
    return tools_node

def make_member_node(agent_name: str, role_prompt: str, tools: list[BaseTool], 
                     llm = MEMBER_DEFAULT_MODEL,
                     return_to_supervisor: bool = True):
    tools = {tool.name: tool for tool in tools}
    tools["notify_supervisor"] = notify_supervisor
    subgraph = StateGraph(State)
    subgraph.add_node(agent_name, make_member_llm_node(agent_name, role_prompt, llm, tools))
    subgraph.add_node("member_human_node", make_member_human_node(agent_name))
    subgraph.add_node("tools", make_member_tools_node(agent_name, tools, return_to_supervisor))
    subgraph.set_entry_point(agent_name)
    subgraph = subgraph.compile()
    return subgraph