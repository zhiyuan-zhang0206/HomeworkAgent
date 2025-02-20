from langchain_core.tools import tool
from loguru import logger
@tool
def notify_supervisor(summary: str) -> str:
    """
    Notify the Supervisor, either to request additional help or to indicate task completion.
    The provided summary describes the request/completion details.
    When this tool is called, control will be transferred to the Supervisor.

    Args:
        summary (str):
            If help is needed, describe the difficulties or questions here;
            If task is completed, provide a summary of the results.
    """
    logger.info(f"Notifying supervisor with summary: {summary}")
    return "Supervisor has been notified."