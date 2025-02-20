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
    
    return config

CONFIG = load_config()

MEMORY_ENABLE_UPDATER = CONFIG["features"]["memory"]["enable_updater"]
MEMORY_ENABLE_RETRIEVAL = CONFIG["features"]["memory"]["enable_retrieval"]
MEMORY_ENABLE_PINECONE_UPDATE = CONFIG["features"]["memory"]["enable_pinecone_update"]
EMAIL_DRAFT_MODE = CONFIG["features"]["email"]["draft_mode"]
USER_EMAIL = CONFIG["features"]["email"]["user_email"]

logger.info(f"Loaded configuration: {CONFIG}") 