import yaml
from pathlib import Path
from loguru import logger

def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    if "features" not in config:
        config["features"] = {}
    if "llms" not in config:
        config["llms"] = {}
    
    features = config["features"]
    llms = config["llms"]
    
    if "memory" not in features:
        features["memory"] = {}
    if "email" not in features:
        features["email"] = {}

    required_llm_configs = [
        "memory_relevance_model",
        "supervisor_model",
        "member_default_model",
        "memory_processor_model",
        "math_agent_model",
        "image_description_model",
        "json_ensure_model"
    ]
    
    for key in required_llm_configs:
        llms.setdefault(key, "gemini-2.0-flash-thinking-exp")
        
    memory_config = features["memory"]
    email_config = features["email"]
    
    # Set memory feature defaults
    memory_config.setdefault("enable_updater", True)
    memory_config.setdefault("enable_retrieval", True)
    memory_config.setdefault("enable_pinecone_update", True)
    
    # Set email feature defaults
    email_config.setdefault("draft_mode", True)
    
    return config

CONFIG = load_config()

MEMORY_ENABLE_UPDATER = CONFIG["features"]["memory"]["enable_updater"]
MEMORY_ENABLE_RETRIEVAL = CONFIG["features"]["memory"]["enable_retrieval"]
MEMORY_ENABLE_PINECONE_UPDATE = CONFIG["features"]["memory"]["enable_pinecone_update"]
EMAIL_DRAFT_MODE = CONFIG["features"]["email"]["draft_mode"]
USER_EMAIL = CONFIG["features"]["email"]["user_email"]

logger.info(f"Loaded configuration: {CONFIG}") 