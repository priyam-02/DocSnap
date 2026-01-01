import asyncio
from io import BytesIO

import pdfplumber


def _extract_text_sync(file_bytes: bytes) -> str:
    """
    Synchronous PDF extraction (runs in thread pool).

    Args:
        file_bytes: Raw bytes of the PDF file

    Returns:
        Extracted text from all pages

    Raises:
        Exception: If PDF extraction fails
    """
    pdf_file = BytesIO(file_bytes)

    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


async def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """
    Extract text from PDF bytes asynchronously.

    Wraps synchronous pdfplumber operations in a thread pool to avoid
    blocking the async event loop.

    Args:
        file_bytes: Raw bytes of the PDF file

    Returns:
        Extracted text from all pages

    Raises:
        ValueError: If PDF extraction fails
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _extract_text_sync, file_bytes)
