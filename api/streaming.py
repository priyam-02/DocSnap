import json
from typing import AsyncIterator

from .logger import setup_logging
from .utils.formatter import format_summary_to_paragraphs
from .utils.pdf_extractor import extract_text_from_pdf_bytes
from .utils.summarizer import summarize_text_streaming

logger = setup_logging()


async def summarize_stream_generator(
    file_bytes: bytes, filename: str, length_option: str, tone_option: str
) -> AsyncIterator[dict]:
    """
    Generate SSE events for streaming summarization.

    Yields events:
    - extraction_started: PDF extraction beginning
    - extraction_complete: PDF extraction done, includes text preview
    - chunk_processing: Processing chunk N of M
    - chunk_complete: Chunk N summary ready
    - formatting: Formatting final summary
    - complete: Final formatted summary
    - error: Error occurred

    Args:
        file_bytes: PDF file content
        filename: Original filename
        length_option: Summary length (Short/Medium/Long)
        tone_option: Summary tone (Neutral/Professional/Casual)

    Yields:
        SSE event dictionaries with 'event' and 'data' keys
    """
    try:
        # Step 1: Extract text
        yield {
            "event": "extraction_started",
            "data": json.dumps({"message": "Extracting text from PDF..."}),
        }

        text = await extract_text_from_pdf_bytes(file_bytes)
        word_count = len(text.split())

        if not text.strip():
            yield {
                "event": "error",
                "data": json.dumps(
                    {"message": "No text found in PDF. The file may contain only images."}
                ),
            }
            return

        yield {
            "event": "extraction_complete",
            "data": json.dumps(
                {
                    "message": "Text extracted successfully",
                    "word_count": word_count,
                    "preview": text[:500] + ("..." if len(text) > 500 else ""),
                }
            ),
        }

        # Step 2: Summarize with streaming
        summary_parts = []
        async for event in summarize_text_streaming(text, length_option, tone_option):
            if event["type"] == "chunk_start":
                yield {
                    "event": "chunk_processing",
                    "data": json.dumps(
                        {
                            "message": f"Processing chunk {event['chunk_index'] + 1} of {event['total_chunks']}",
                            "progress": (event["chunk_index"] / event["total_chunks"]) * 100,
                        }
                    ),
                }
            elif event["type"] == "chunk_complete":
                summary_parts.append(event["summary"])
                yield {
                    "event": "chunk_complete",
                    "data": json.dumps(
                        {
                            "message": f"Chunk {event['chunk_index'] + 1} summarized",
                            "summary": event["summary"],
                            "progress": (
                                (event["chunk_index"] + 1) / event["total_chunks"]
                            )
                            * 100,
                        }
                    ),
                }

        # Step 3: Format summary
        yield {
            "event": "formatting",
            "data": json.dumps({"message": "Formatting summary..."}),
        }

        full_summary = " ".join(summary_parts)
        formatted = format_summary_to_paragraphs(full_summary)

        # Step 4: Complete
        yield {
            "event": "complete",
            "data": json.dumps(
                {
                    "summary": full_summary,
                    "formatted_summary": formatted,
                    "extracted_text_preview": text[:500] + ("..." if len(text) > 500 else ""),
                    "metadata": {
                        "original_word_count": word_count,
                        "summary_word_count": len(full_summary.split()),
                        "compression_ratio": round(len(full_summary) / len(text), 3),
                    },
                }
            ),
        }

        logger.info("streaming_complete", filename=filename)

    except Exception as e:
        logger.error("streaming_error", error=str(e), filename=filename)
        yield {
            "event": "error",
            "data": json.dumps({"message": f"Error: {str(e)}"}),
        }
