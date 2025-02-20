from langchain_core.tools import tool
from pathlib import Path
from PIL import Image
from io import BytesIO
import os
import time
from difflib import SequenceMatcher

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from loguru import logger
from msrest.authentication import CognitiveServicesCredentials

def _ocr(image:Image.Image) -> list[dict]:
    computervision_client = ComputerVisionClient(
        os.environ["AZURE_VISION_ENDPOINT"], 
        CognitiveServicesCredentials(os.environ["AZURE_VISION_KEY"])
    )

    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format=image.format or 'PNG')
    img_byte_arr.seek(0)
    
    read_response = computervision_client.read_in_stream(img_byte_arr, raw=True)

    read_operation_location = read_response.headers["Operation-Location"]
    operation_id = read_operation_location.split("/")[-1]

    while True:
        read_result = computervision_client.get_read_result(operation_id)
        if read_result.status not in [OperationStatusCodes.not_started, OperationStatusCodes.running]:
            break
        time.sleep(0.2)

    if read_result.status == OperationStatusCodes.succeeded:
        return read_result.as_dict()['analyze_result']['read_results'][0]['lines']
    else:
        return OperationStatusCodes.failed

def _similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

@tool
def perform_ocr(image_path:str) -> list[str]:
    '''
    Read the text from the image.
    Returns:
        A list of (text, center) pairs containing the text and the center of the text.
    
    Args:
        image_path: The image to read the text from.
    '''
    logger.info(f"Performing OCR on image {image_path}.")
    image = Image.open(image_path)
    data = _ocr(image)
    results = []
    for line in data:
        text = line['text']
        center = (int(sum(line['bounding_box'][0::2])//4), int(sum(line['bounding_box'][1::2])//4))
        results.append((text, center))
    logger.info(f"OCR results: {results}")
    return results

@tool
def locate_text(image_path:str, text:str, top_k:int=3) -> dict:
    '''
    Locate the text in the image.
    Returns:
        A list of dictionaries containing the score, text, center of the text.

    Args:
        image_path: The path to the image to locate the text in.
        text: The text to locate.
        top_k: Optional. The number of top results to return.
    '''
    logger.info(f"Locating text {text} in image {image_path} with top_k={top_k}.")
    image = Image.open(image_path)
    data = _ocr(image)
    texts_and_words = set()
    for line in data:
        texts_and_words.add((line['text'].lower(), tuple(line['bounding_box'])))
        for word in line['words']:
            texts_and_words.add((word['text'].lower(), tuple(word['bounding_box'])))

    text_words_similarity = set()
    for d in texts_and_words:
        text_words_similarity.add((_similarity(d[0], text.lower()), *d))

    text_words_similarity = list(text_words_similarity)
    text_words_similarity.sort(key=lambda x: x[0], reverse=True)
    top_results = text_words_similarity[:top_k]
    centers = [(sum(bounding_box[0::2])//4, sum(bounding_box[1::2])//4) for _, _, bounding_box in top_results]
    final_results = [{"score": score, 
                     "text": text, 
                     "center": center,
                     # "bounding_box": bounding_box
                     } for (score, text, bounding_box), center in zip(top_results, centers)]
    logger.info(f"Located text in image {image_path}: {final_results}")
    return final_results

__all__ = ["perform_ocr", 
           "locate_text"]

