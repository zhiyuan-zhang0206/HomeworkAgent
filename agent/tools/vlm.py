import time
from langchain_core.tools import tool
from PIL import Image
from .images import get_image_url
from langchain_core.messages import HumanMessage
from loguru import logger
from ..llms import IMAGE_DESCRIPTION_MODEL

@tool
def get_image_description(
    filepath: str,
    additional_prompt: str = ""
) -> str:
    """
    Get the description of an image. Calls GPT-4o to describe the image.

    Args:
        filepath: str
            The path to the image file.
    """
    logger.info(f"Getting image description for {filepath}")
    start_time = time.time()
    image = Image.open(filepath)
    text_prompt = f"Describe the image in detail. {additional_prompt}"

    result = IMAGE_DESCRIPTION_MODEL.invoke(
        [
            HumanMessage(
                content=[
                    {"type": "text", "text": text_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": get_image_url(image),
                            "detail": "high",
                        },
                    },
                ]
            )
        ]
    )
    logger.info(f"Image description: {result.content}")
    logger.info(f"Time taken: {time.time() - start_time} seconds")
    return result.content
