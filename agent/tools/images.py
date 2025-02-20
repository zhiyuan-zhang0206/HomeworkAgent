
import base64
import io
import numpy as np
import cv2
from loguru import logger
from pathlib import Path
from PIL import Image

def open_image(path: str) -> Image.Image:
    '''
    Read an image from a file.
    - args:
        - path: str
            The path to the image file.
    - returns:
        - image: The image object. If the file does not exist, return an error message.
    '''
    path = Path(path).expanduser().resolve()
    if not path.exists():
        return f'File {path} does not exist.'
    image = Image.open(path)
    return image

def get_base64_image(image: Image.Image) -> str:
    '''
    Get the base64 encoded image.
    - args:
        - image: Image.Image
            The PIL image object.
    - returns:
        - str: The base64 encoded image.
    '''
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    base64_image = base64.b64encode(img_byte_arr).decode('utf-8')
    return base64_image

def get_image_url(image: Image.Image) -> str:
    return f'data:image/png;base64,{get_base64_image(image)}'

def load_base64_image(base64_image: str) -> Image.Image:
    '''
    Load a base64 encoded image.
    - args:
        - base64_image: str
            The base64 encoded image.
    - returns:
        - image: Image.Image
            The image object.
    '''
    return Image.open(io.BytesIO(base64.b64decode(base64_image)))

__all__ = ['open_image', 
           'get_base64_image', 
           'get_image_url']
