from langchain_core.tools import tool
from loguru import logger
from ..timestamp import get_current_timestamp
import os
from pinecone import Pinecone
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pinecone.core.openapi.shared.exceptions import ServiceException
from agent.config import MEMORY_ENABLE_PINECONE_UPDATE

MEMORY_SCORE_THRESHOLD = 0.8
logger.info(f"Pinecone memory update is {'enabled' if MEMORY_ENABLE_PINECONE_UPDATE else 'disabled'}")

class PineconeMemoryManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.pc = Pinecone(api_key=os.environ['PINECONE_API_KEY'])
            cls._instance.index = cls._instance.pc.Index("agent-long-term-memory")
        return cls._instance

    def __init__(self):
        pass

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(ServiceException)
    )
    def _embed_text(self, text, input_type="passage"):
        """Helper method to embed text with retry logic"""
        return self.pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[text],
            parameters={"input_type": input_type, "truncate": "END"}
        )

    def add_memory(self, memory:str, id:str=None):
        logger.info(f"Embedding memory: {memory}")
        embeddings = self._embed_text(memory)
        logger.info(f"Upserting memory...")
        if not MEMORY_ENABLE_PINECONE_UPDATE:
            logger.info("Memory update is disabled.")
            return
        self.index.upsert(
            vectors=[{"id": id or get_current_timestamp(include_milliseconds=True), "values": embeddings[0]['values'], "metadata": {"text": memory}}]
        )

    def update_memory(self, id:str, content:str):
        logger.info(f"Updating memory id: {id}, content: {content}")
        if not MEMORY_ENABLE_PINECONE_UPDATE:
            logger.info("Memory update is disabled.")
            return
        embeddings = self._embed_text(content)
        self.index.upsert(
            vectors=[{"id": id, "values": embeddings[0]['values'], "metadata": {"text": content}}]
        )

    def query_memory(self, query:str, top_k:int=3, exclude_ids:set[str]=set()):
        if exclude_ids is None:
            exclude_ids = set()
        else:
            exclude_ids = set(exclude_ids)

        query_embedding = self._embed_text(query, input_type="query")

        current_top_k = top_k
        if exclude_ids:
            current_top_k = top_k + len(exclude_ids)

        query_results = self.index.query(
            vector=query_embedding[0].values,
            top_k=current_top_k,
            include_metadata=True,
            include_values=False
        )
        logger.info(f"Pinecone query: \"{query}\"\n\n\nQuery results: {query_results}")
        results = []
        for result in query_results['matches']:
            if len(results) >= top_k:
                break
            if result['score'] < MEMORY_SCORE_THRESHOLD:
                continue
            memory_id = result['id']
            if memory_id not in exclude_ids:
                results.append({
                    "id": memory_id,
                    "content": result['metadata']['text']
                })

        return results
    
    def delete_memory(self, id:str):
        logger.info(f"Deleting memory id: {id}")
        if not MEMORY_ENABLE_PINECONE_UPDATE:
            logger.info("Memory update is disabled.")
            return
        self.index.delete(ids=[id])
        return f"Memory deleted successfully. ID: {id}"

    def fetch_all_memories(self):
        ids = [id_ for id_ in self.index.list()]
        memories = self.index.fetch(ids=ids)
        return memories

MEMORIES_DIR_NAME = 'memories'
DELETED_MEMORIES_DIR_NAME = 'deleted_memories'


@tool
def delete_memory(memory_id:str) -> str:
    '''
    Delete a piece of memory from long term memory.

    Args:
        memory_id: The id of the memory to delete.
    '''
    pinecone_memory_manager = PineconeMemoryManager()
    pinecone_memory_manager.delete_memory(memory_id)
    return f"Memory deleted successfully. ID: {memory_id}"

@tool
def update_memory(memory_id:str, content:str) -> str:
    '''
    Update a piece of memory in long term memory.
    
    Args:
        memory_id: str
            The id of the memory to update.
        content: str
            The new content of the memory.
    '''
    pinecone_memory_manager = PineconeMemoryManager()
    pinecone_memory_manager.update_memory(memory_id, content)
    return f"Memory updated successfully."

@tool
def add_memory(memory:str) -> str:
    '''
    Add a piece of memory to long term memory.

    Args:
        memory: str
            The memory to add.
    '''

    timestamp = get_current_timestamp(include_milliseconds=True)
    pinecone_memory_manager = PineconeMemoryManager()
    pinecone_memory_manager.add_memory(memory, id=timestamp)
    return f"Memory added successfully." 

@tool
def search_memory(query:str, top_k:int=3, exclude_ids:set[str]=set()) -> str:
    '''
    Search for a piece of memory in long term memory.
    This is supported by Pinecone's vector search.

    Args:
        query: The query to search for.
    '''
    pinecone_memory_manager = PineconeMemoryManager()
    results = pinecone_memory_manager.query_memory(query, top_k=top_k, exclude_ids=exclude_ids)
    return results


__all__ = ['add_memory', 'search_memory', 'update_memory', 'delete_memory']