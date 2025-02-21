import json
import traceback
from loguru import logger
from langchain_core.messages import HumanMessage
from requests import HTTPError
from openai import RateLimitError
from tenacity import (
    retry as tenacity_retry,
    retry_if_exception,
    stop_after_attempt,
    RetryCallState
)
from requests.exceptions import HTTPError
from openai import RateLimitError, InternalServerError, APIConnectionError
from .llms import JSON_ENSURE_MODEL
import json


class InvalidResponseFormatError(Exception):
    pass

def retry_handler(exception: Exception) -> bool:
    if isinstance(exception, HTTPError):
        status_code = exception.response.status_code
        return status_code in [500]
    return isinstance(exception, (json.JSONDecodeError, # this is for busy deepseek official api
                                  RateLimitError, 
                                  InvalidResponseFormatError, 
                                  InternalServerError, 
                                  APIConnectionError))

def wait_handler(retry_state: RetryCallState) -> float:
    exception = retry_state.outcome.exception()
    if isinstance(exception, HTTPError) and exception.response.status_code == 429:
        return 5
    if isinstance(exception, RateLimitError):
        return 15
    if isinstance(exception, InternalServerError):
        return 60
    if isinstance(exception, APIConnectionError):
        return 10
    return 0.1

def before_retry_log(retry_state: RetryCallState):
    exception = retry_state.outcome.exception()
    logger.warning(f"Retrying due to {exception.__class__.__name__}: {str(exception)}. Stack trace: {traceback.format_exc()}")

retry = tenacity_retry(
    retry=retry_if_exception(retry_handler),
    wait=wait_handler,
    stop=stop_after_attempt(10),
    before_sleep=before_retry_log,
)

@retry
def get_and_parse_json_response(llm, messages) -> tuple[str, dict]:
    logger.info(f"Invoking LLM with last message: \n{messages[-1].content}")
    response = llm.invoke(messages)
    logger.info(f"LLM response: \n{response.content}")
    if response.additional_kwargs.get("reasoning_content"):
        logger.info(f"Reasoning content: {response.additional_kwargs['reasoning_content']}")
    response, parsed = parse_json_response(response.content)
    logger.info(f"Parsed response: \n{json.dumps(parsed, indent=4)}")
    return response, parsed


def split_reasoning_and_response(response: str) -> tuple[str, str]:
    if response.startswith("<think>"):
        thinking_end = response.find("</think>")
        if thinking_end == -1:
            raise InvalidResponseFormatError("Thinking section not end")
        reasoning_content = response[len("<think>"):thinking_end].strip()
        response = response[thinking_end + len("</think>"):].strip()
        logger.info(f"Reasoning: {reasoning_content}")
    else:
        reasoning_content = ""
    return reasoning_content, response

def parse_json_response(response: str) -> tuple[str, dict]:
    response = response.strip()
    reasoning_content, response = split_reasoning_and_response(response)
    response = response.strip().removeprefix("```json").removesuffix("```")
    try:
        parsed = json.loads(response)
    except json.JSONDecodeError:
        logger.warning(f"Response is not a valid JSON object, trying to format it using LLM")
        parsed = ensure_JSON_LLM_call(response)
    return response, parsed

@retry
async def aget_and_parse_json_response(llm, messages):
    logger.info(f"Invoking LLM with last message: \n{messages[-1].content}")
    response = await llm.ainvoke(messages, timeout=30)
    logger.info(f"LLM response: \n{response.content}")
    response, parsed = parse_json_response(response.content)
    logger.info(f"Parsed response: \n{json.dumps(parsed, indent=4)}")
    return response, parsed


ENSURE_JSON_PROMPT = """
You are a JSON formatter.
You will be given a response from an LLM, which might not be a valid JSON object.
Please format the response into a valid JSON object, no explanation is needed.
Here is the response:
"""

def ensure_JSON_LLM_call(response: str) -> dict:
    logger.info(f"Ensuring JSON: {response}")
    result = json.loads(JSON_ENSURE_MODEL.invoke(
        [HumanMessage(content=ENSURE_JSON_PROMPT + response)]
    ).content)
    logger.info(f"Ensured JSON: {result}")
    return result
