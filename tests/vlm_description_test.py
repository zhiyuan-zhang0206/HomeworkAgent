from agent.tools.vlm import get_image_description
from dotenv import load_dotenv
load_dotenv()
if __name__ == "__main__":
    get_image_description.invoke(
        {"filepath": r"xxx.png",
         "context_prompt": ""}
    )
    