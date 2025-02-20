import datetime
from loguru import logger

_current_run_timestamp = None

def get_current_timestamp(include_milliseconds=False):
    now = datetime.datetime.now()
    if include_milliseconds:
        return now.strftime("%Y-%m-%d_%H-%M-%S_%f")[:-3]
    else:
        return now.strftime("%Y-%m-%d_%H-%M-%S")

def get_current_run_timestamp(include_milliseconds=False):
    global _current_run_timestamp
    if _current_run_timestamp is None:
        logger.info(f"Current run timestamp is None, setting to {get_current_timestamp(include_milliseconds)}")
        _current_run_timestamp = get_current_timestamp(include_milliseconds)
    return _current_run_timestamp

__all__ = ['get_current_run_timestamp', 'get_current_timestamp']