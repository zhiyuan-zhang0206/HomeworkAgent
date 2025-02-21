import os
import warnings
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain_xai import ChatXAI
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger
from .config import CONFIG

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning, message=r"WARNING! response_format is not default parameter")

    AVAILABLE_MODELS = {
        "gpt-4o": ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o"
        ),
        "gpt-4o-mini": ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini"
        ),
        "gpt-4o-json": ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o",
            response_format={ "type": "json_object" }
        ),
        "gpt-4o-mini-json": ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
            response_format={ "type": "json_object" }
        ),
        "claude-3-5-sonnet": ChatAnthropic(
            model="claude-3-5-sonnet-latest",
        ),
        "o1": ChatOpenAI(
            model="o1",
            api_key=os.getenv("OPENAI_API_KEY"),
        ),
        "o3-mini": ChatOpenAI(
            model="o3-mini",
            reasoning_effort="high",
            api_key=os.getenv("OPENAI_API_KEY"),
        ),
        "deepseek-chat": ChatDeepSeek(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            model="deepseek-chat"
        ),
        "deepseek-reasoner": ChatDeepSeek(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            model="deepseek-reasoner",
            max_tokens=8192
        ),
        "deepseek-chat-sf": ChatOpenAI(
            model="deepseek-ai/DeepSeek-V3",
            api_key=os.getenv("SILICON_FLOW_API_KEY"),
            base_url="https://api.siliconflow.cn/v1"
        ),
        "deepseek-reasoner-sf": ChatOpenAI(
            model="deepseek-ai/DeepSeek-R1",
            api_key=os.getenv("SILICON_FLOW_API_KEY"),
            base_url="https://api.siliconflow.cn/v1",
            max_tokens=8192
        ),
        "deepseek-reasoner-bce": ChatOpenAI(
            api_key=os.getenv("BCE_API_KEY"),
            model="deepseek-r1",
            base_url="https://qianfan.baidubce.com/v2"
        ),
        "grok-2": ChatXAI(
            model="grok-2-latest",
            api_key=os.getenv("XAI_API_KEY"),
        ),
        "gemini-2.0-flash-thinking-exp": ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-thinking-exp-01-21",
            api_key=os.getenv("GEMINI_API_KEY"),
        ),
        "gemini-2.0-flash": ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            api_key=os.getenv("GEMINI_API_KEY"),
        ),
        "deepseek-reasoner-openrouter": ChatOpenAI(
            model="deepseek/deepseek-r1:free",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        ),
    }

try:
    llms_config = CONFIG["llms"]
    
    required_configs = [
        "memory_relevance_model",
        "supervisor_model",
        "member_default_model",
        "memory_processor_model",
        "math_agent_model",
        "image_description_model",
        "json_ensure_model"
    ]
    
    for key in required_configs:
        if key not in llms_config:
            raise KeyError(f"Missing required configuration: {key}")
        if llms_config[key] not in AVAILABLE_MODELS:
            raise ValueError(f"Model '{llms_config[key]}' specified for {key} is not available")
    
    MEMORY_RELEVANCE_MODEL = AVAILABLE_MODELS[llms_config["memory_relevance_model"]]
    SUPERVISOR_MODEL = AVAILABLE_MODELS[llms_config["supervisor_model"]]
    MEMBER_DEFAULT_MODEL = AVAILABLE_MODELS[llms_config["member_default_model"]]
    MEMORY_PROCESSOR_MODEL = AVAILABLE_MODELS[llms_config["memory_processor_model"]]
    MATH_AGENT_MODEL = AVAILABLE_MODELS[llms_config["math_agent_model"]]
    IMAGE_DESCRIPTION_MODEL = AVAILABLE_MODELS[llms_config["image_description_model"]]
    JSON_ENSURE_MODEL = AVAILABLE_MODELS[llms_config["json_ensure_model"]]
    
    logger.info("Successfully loaded model configuration")

except Exception as e:
    logger.error(f"Error loading model configuration: {str(e)}")
    raise

__all__ = [
    "MEMORY_RELEVANCE_MODEL",
    "SUPERVISOR_MODEL",
    "MEMBER_DEFAULT_MODEL",
    "IMAGE_DESCRIPTION_MODEL",
    "MEMORY_PROCESSOR_MODEL",
    "MATH_AGENT_MODEL",
    "JSON_ENSURE_MODEL",
]