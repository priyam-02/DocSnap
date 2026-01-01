import os
from typing import AsyncIterator, Literal

import httpx

# Reuse from app.py lines 44-52
LENGTH_SETTINGS = {
    "Short": {"max_len": 60, "min_len": 30},
    "Medium": {"max_len": 120, "min_len": 50},
    "Long": {"max_len": 200, "min_len": 80},
}

# Reuse from app.py lines 56-61
TONE_INSTRUCTIONS = {
    "Neutral": "Summarize the following content clearly and concisely:",
    "Professional": "Write a formal and professional executive summary of the following content:",
    "Casual": "Explain the following content in a friendly and easy-to-understand tone:",
}


async def summarize_text_async(
    text: str,
    length_option: Literal["Short", "Medium", "Long"] = "Medium",
    tone_option: Literal["Neutral", "Professional", "Casual"] = "Neutral",
    max_chunk_size: int = 1000,
) -> str:
    """
    Summarize text using Hugging Face Inference API.

    Replaces the local transformers pipeline (app.py lines 38-69) with
    API calls to avoid the 1.6GB model size issue on Vercel.

    Args:
        text: Text to summarize
        length_option: Summary length (Short, Medium, Long)
        tone_option: Summary tone (Neutral, Professional, Casual)
        max_chunk_size: Maximum characters per chunk

    Returns:
        Summarized text

    Raises:
        httpx.HTTPError: If HF API request fails
        KeyError: If HF_API_TOKEN environment variable is not set
    """
    HF_API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"

    api_token = os.getenv("HF_API_TOKEN")
    if not api_token:
        raise KeyError("HF_API_TOKEN environment variable not set")

    headers = {"Authorization": f"Bearer {api_token}"}

    # Chunk text (same strategy as original app.py:41)
    chunks = [text[i : i + max_chunk_size] for i in range(0, len(text), max_chunk_size)]

    settings = LENGTH_SETTINGS[length_option]
    instruction = TONE_INSTRUCTIONS[tone_option]

    async with httpx.AsyncClient(timeout=30.0) as client:
        summary = ""
        for i, chunk in enumerate(chunks):
            prompt = f"{instruction} {chunk}"
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": settings["max_len"],
                    "min_length": settings["min_len"],
                    "do_sample": False,
                },
            }

            try:
                response = await client.post(HF_API_URL, headers=headers, json=payload)
                response.raise_for_status()

                result = response.json()
                # Validate response structure
                if isinstance(result, list) and len(result) > 0 and "summary_text" in result[0]:
                    summary += result[0]["summary_text"] + " "
                else:
                    raise ValueError(f"Unexpected HF API response format: {result}")

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    raise Exception("Rate limit exceeded. Please try again later.")
                elif e.response.status_code == 503:
                    raise Exception(
                        "Hugging Face API is temporarily unavailable. Please try again."
                    )
                else:
                    raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
            except httpx.TimeoutException:
                raise Exception(f"Timeout while processing chunk {i+1}/{len(chunks)}")

    return summary.strip()


async def summarize_text_streaming(
    text: str,
    length_option: Literal["Short", "Medium", "Long"] = "Medium",
    tone_option: Literal["Neutral", "Professional", "Casual"] = "Neutral",
    max_chunk_size: int = 1000,
) -> AsyncIterator[dict]:
    """
    Streaming version of summarize_text_async.

    Yields events as chunks are processed:
    - {"type": "chunk_start", "chunk_index": 0, "total_chunks": 5}
    - {"type": "chunk_complete", "chunk_index": 0, "summary": "..."}

    Args:
        text: Text to summarize
        length_option: Summary length (Short, Medium, Long)
        tone_option: Summary tone (Neutral, Professional, Casual)
        max_chunk_size: Maximum characters per chunk

    Yields:
        Dictionary events with type, chunk_index, and data
    """
    HF_API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"

    api_token = os.getenv("HF_API_TOKEN")
    if not api_token:
        raise KeyError("HF_API_TOKEN environment variable not set")

    headers = {"Authorization": f"Bearer {api_token}"}
    chunks = [text[i : i + max_chunk_size] for i in range(0, len(text), max_chunk_size)]
    settings = LENGTH_SETTINGS[length_option]
    instruction = TONE_INSTRUCTIONS[tone_option]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, chunk in enumerate(chunks):
            # Notify chunk started
            yield {"type": "chunk_start", "chunk_index": i, "total_chunks": len(chunks)}

            prompt = f"{instruction} {chunk}"
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": settings["max_len"],
                    "min_length": settings["min_len"],
                    "do_sample": False,
                },
            }

            try:
                response = await client.post(HF_API_URL, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()

                if isinstance(result, list) and len(result) > 0 and "summary_text" in result[0]:
                    summary = result[0]["summary_text"]

                    # Notify chunk complete
                    yield {
                        "type": "chunk_complete",
                        "chunk_index": i,
                        "summary": summary,
                        "total_chunks": len(chunks),
                    }
                else:
                    raise ValueError(f"Unexpected response format: {result}")

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    raise Exception("Rate limit exceeded. Please try again later.")
                elif e.response.status_code == 503:
                    raise Exception(
                        "Hugging Face API is temporarily unavailable. Please try again."
                    )
                else:
                    raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
            except httpx.TimeoutException:
                raise Exception(f"Timeout while processing chunk {i+1}/{len(chunks)}")
