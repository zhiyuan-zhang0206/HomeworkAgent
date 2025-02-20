from dotenv import load_dotenv
from agent.tools.ocr import perform_ocr

if __name__ == "__main__":
    load_dotenv()
    read_image_path = r"..."
    print(perform_ocr.invoke({"image_path": read_image_path}))