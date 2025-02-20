import time
import warnings
from langchain_core.tools import tool
from pathlib import Path
from loguru import logger
import warnings
import asyncio
import tempfile
async def pdf_to_markdown(file_path: str, select_pages: int | list[int] | None = None, output_dir: str | None = None) -> str:
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            category=UserWarning,
            message=r"Valid config keys have changed in V2:.*"
        )
        from pyzerox import zerox # lazy import, as this is very time consuming
    custom_system_prompt = """
    Convert the following PDF page to markdown.
    Return only the markdown with no explanation text.
    Do not exclude any content from the page.

    Use "$ ... $" for inline math symbols or expressions, and "$$ ... $$" for multiline math expressions, do not use "\\( ... \\)" or "\\[ ... \\]" anywhere in your response.
    """

    model = "gpt-4o-mini"

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            category=UserWarning,
            message=r"Custom system prompt was provided which overrides the default system prompt.*"
        )
        result = await zerox(
            file_path=file_path,
            model=model,
            output_dir=output_dir,
            custom_system_prompt=custom_system_prompt,
            select_pages=select_pages
        )
    return result

@tool
def convert_pdf2md(file_path: str, save_path: str, pages: int | list[int] | None = None) -> str:
    '''
    Convert PDF file to markdown format.
    Args:
        file_path: str
            Path to the PDF file.
        save_path: str
            File path to save the converted markdown file.
        pages: int | list[int] | None
            Pages to convert. If None, all pages will be converted.
    '''
    file_path = Path(file_path).expanduser().resolve()
    logger.info(f"Converting PDF to markdown: {file_path.as_posix()}")
    start_time = time.time()
    if not file_path.exists():
        return f"File not found: {file_path.as_posix()}"
    if not file_path.suffix == '.pdf':
        return f"File is not a PDF: {file_path.as_posix()}"
    save_path = Path(save_path).expanduser().resolve()
    if not save_path.parent.exists():
        save_path.parent.mkdir(parents=True, exist_ok=True)
    if save_path.exists():
        return f"File already exists: {save_path.as_posix()}"
    # Create temporary directory for intermediate output
    with tempfile.TemporaryDirectory() as temp_dir:

        result = asyncio.run(pdf_to_markdown(file_path.as_posix(), pages, temp_dir))
        temp_file = Path(temp_dir) / (result.file_name + '.md')
        try:
            with open(temp_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(temp_file, 'r', encoding='latin-1') as f:
                content = f.read()
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(content)
    end_time = time.time()
    logger.info(f"Conversion complete. Saved to {save_path.as_posix()}. Time taken: {end_time - start_time:.2f} seconds")
    return f"Converted file: {file_path.as_posix()}, saved to {save_path.as_posix()}"

__all__ = [
    "convert_pdf2md"
]