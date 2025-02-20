from agent.tools.pdf2md import convert_pdf2md
from dotenv import load_dotenv
load_dotenv()

result = convert_pdf2md.invoke(
    {"file_path": r"xxx.pdf", 
     "save_path": r"xxx.md"}
)
print(result)