from loguru import logger
import asyncio
from langchain_core.messages import HumanMessage, AnyMessage
from ..tools.memory import search_memory
from ..llms import MEMORY_RELEVANCE_MODEL
from ..llm_calling import aget_and_parse_json_response
from agent.config import MEMORY_ENABLE_RETRIEVAL

logger.info(f"Memory retrieval is {'enabled' if MEMORY_ENABLE_RETRIEVAL else 'disabled'}")

MEMORY_ROLE_PROMPT = """
You will act as a memory agent.
You are responsible for maintaining and retrieving information from previous conversations and interactions.
Your main responsibilities are:
1. Store important information from conversations and interactions
2. Retrieve relevant information when needed
3. Maintain context and history of interactions
4. Help other agents access historical information when needed
"""

MEMORY_AGENT_NAME = "memory_agent"

MEMORY_AGENT_ABILITIES = "memory_agent can search or update the long-term memory of this agent."


async def _aget_memory_relevant_decision(context: str, memory_content: str, llm) -> tuple[str, str]:
    relevance_prompt = f"""
You are an AI agent responsible for evaluating the helpfulness of memories in a system.
Your task is to determine if a specific memory is relevant to the current context. Only exclude completely irrelevant memories.
The context will be given in the form of messages between the agent and the system.

Respond in JSON.
You should respond a JSON object with the following fields:
- "thoughts": your analysis of the memory and context, why it is potentially helpful or not
- "decision": "YES" or "NO"

Example response:
{{
    "thoughts": "The context is about the user's request that... And the memory is about... So it is potentially helpful.",
    "decision": "YES"
}}

The context will follow the "Current Context" section, and the memory content will follow the "Memory Content" section.

Current Context:
{context}

Memory Content:
{memory_content}
    """
    response, parsed = await aget_and_parse_json_response(llm, [HumanMessage(content=relevance_prompt)])
    thoughts = parsed["thoughts"]
    decision = parsed["decision"]
    return thoughts, decision

def get_relevant_memories(messages: list[AnyMessage], 
                          top_k: int = 5, 
                          exclude_ids: list[str] = None) -> tuple[list[dict], list[str], str]:
    if not MEMORY_ENABLE_RETRIEVAL:
        logger.info("Memory retrieval is disabled, returning empty results.")
        return [], [], ""
    context = "\n".join([f"{'System' if msg.type == 'human' else 'Agent'}: {msg.content}"
                     for msg in messages[-2:] if msg.type != 'system'])
    logger.info(f'Retrieving relevant memories with query={context}, top_k={top_k}, exclude_ids={exclude_ids}')
    search_results = search_memory.invoke({"query": context, "top_k": top_k, "exclude_ids": exclude_ids})
    if not search_results:
        logger.info("No relevant memories found by Pinecone.")
        return [], [], ""
    
    llm = MEMORY_RELEVANCE_MODEL
    
    async def _process_memories():
        return await asyncio.gather(*[
            _aget_memory_relevant_decision(
                context=context,
                memory_content=memory.get('content'),
                llm=llm
            )
            for memory in search_results
        ])
    
    logger.info(f"Waiting for LLM memory helpfulness decisions... total {len(search_results)} memories")
    decisions = asyncio.run(_process_memories())

    relevant_memories = []
    for memory, (thoughts, decision) in zip(search_results, decisions):
        if decision == "YES":
            relevant_memories.append(memory)
        elif decision == "NO":
            pass
        else:
            raise ValueError(f"Invalid decision: {decision}") # TODO: handle this
    logger.info(f"Found {len(relevant_memories)} / {len(search_results)} relevant memories")
    memory_ids = [memory.get("id") for memory in relevant_memories]
    formatted_memories = []
    for memory in relevant_memories:
        formatted_memories.append(f"Memory ID: {memory.get('id')}\nMemory Content: {memory.get('content')}")
    if formatted_memories:
        formatted_memories = "\n\nRelevant long-term memories:\n"+"\n\n".join(formatted_memories)
    else:
        formatted_memories = ""
    return relevant_memories, memory_ids, formatted_memories