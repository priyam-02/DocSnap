import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from api.utils.summarizer import summarize_text_async, summarize_text_streaming


@pytest.mark.asyncio
async def test_summarize_text_async(mock_hf_token):
    """Test summarization with mocked HF API"""
    with patch("api.utils.summarizer.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = [{"summary_text": "Test summary"}]
        mock_response.raise_for_status.return_value = None

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        result = await summarize_text_async(
            "This is a test document with some content.", "Medium", "Neutral"
        )

        assert result.strip() == "Test summary"


@pytest.mark.asyncio
async def test_summarize_chunking(mock_hf_token):
    """Test that long text is properly chunked"""
    long_text = "word " * 500  # 500 words, should create multiple chunks

    with patch("api.utils.summarizer.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = [{"summary_text": "Chunk summary"}]
        mock_response.raise_for_status.return_value = None

        mock_post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.post = mock_post

        await summarize_text_async(long_text, "Medium", "Neutral")

        # Verify multiple API calls were made (chunking)
        assert mock_post.call_count > 1


@pytest.mark.asyncio
async def test_summarize_different_lengths(mock_hf_token):
    """Test different length options"""
    with patch("api.utils.summarizer.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = [{"summary_text": "Summary"}]
        mock_response.raise_for_status.return_value = None

        mock_post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.post = mock_post

        # Test Short
        await summarize_text_async("Test text", "Short", "Neutral")
        call_args = mock_post.call_args[1]["json"]["parameters"]
        assert call_args["max_length"] == 60

        # Test Medium
        await summarize_text_async("Test text", "Medium", "Neutral")
        call_args = mock_post.call_args[1]["json"]["parameters"]
        assert call_args["max_length"] == 120

        # Test Long
        await summarize_text_async("Test text", "Long", "Neutral")
        call_args = mock_post.call_args[1]["json"]["parameters"]
        assert call_args["max_length"] == 200


@pytest.mark.asyncio
async def test_summarize_different_tones(mock_hf_token):
    """Test different tone options"""
    with patch("api.utils.summarizer.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = [{"summary_text": "Summary"}]
        mock_response.raise_for_status.return_value = None

        mock_post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.post = mock_post

        # Test Neutral
        await summarize_text_async("Test text", "Medium", "Neutral")
        prompt = mock_post.call_args[1]["json"]["inputs"]
        assert "Summarize" in prompt

        # Test Professional
        await summarize_text_async("Test text", "Medium", "Professional")
        prompt = mock_post.call_args[1]["json"]["inputs"]
        assert "formal" in prompt.lower()

        # Test Casual
        await summarize_text_async("Test text", "Medium", "Casual")
        prompt = mock_post.call_args[1]["json"]["inputs"]
        assert "friendly" in prompt.lower()


@pytest.mark.asyncio
async def test_summarize_missing_api_token(monkeypatch):
    """Test error when HF_API_TOKEN is not set"""
    monkeypatch.delenv("HF_API_TOKEN", raising=False)

    with pytest.raises(KeyError, match="HF_API_TOKEN"):
        await summarize_text_async("Test text", "Medium", "Neutral")


@pytest.mark.asyncio
async def test_summarize_api_rate_limit(mock_hf_token):
    """Test handling of rate limit errors"""
    with patch("api.utils.summarizer.httpx.AsyncClient") as mock_client:
        from httpx import HTTPStatusError

        mock_response = MagicMock()
        mock_response.status_code = 429

        mock_post = AsyncMock(
            side_effect=HTTPStatusError(
                "Rate limit exceeded",
                request=MagicMock(),
                response=mock_response,
            )
        )
        mock_client.return_value.__aenter__.return_value.post = mock_post

        with pytest.raises(Exception, match="Rate limit exceeded"):
            await summarize_text_async("Test text", "Medium", "Neutral")


@pytest.mark.asyncio
async def test_summarize_api_unavailable(mock_hf_token):
    """Test handling of API unavailability (503)"""
    with patch("api.utils.summarizer.httpx.AsyncClient") as mock_client:
        from httpx import HTTPStatusError

        mock_response = MagicMock()
        mock_response.status_code = 503

        mock_post = AsyncMock(
            side_effect=HTTPStatusError(
                "Service Unavailable",
                request=MagicMock(),
                response=mock_response,
            )
        )
        mock_client.return_value.__aenter__.return_value.post = mock_post

        with pytest.raises(Exception, match="temporarily unavailable"):
            await summarize_text_async("Test text", "Medium", "Neutral")


@pytest.mark.asyncio
async def test_summarize_streaming(mock_hf_token):
    """Test streaming summarization yields events"""
    with patch("api.utils.summarizer.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = [{"summary_text": "Chunk summary"}]
        mock_response.raise_for_status.return_value = None

        mock_post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.post = mock_post

        events = []
        async for event in summarize_text_streaming("Test text", "Medium", "Neutral"):
            events.append(event)

        # Should get chunk_start and chunk_complete events
        assert len(events) == 2
        assert events[0]["type"] == "chunk_start"
        assert events[1]["type"] == "chunk_complete"
        assert "summary" in events[1]


@pytest.mark.asyncio
async def test_summarize_streaming_multiple_chunks(mock_hf_token):
    """Test streaming with multiple chunks"""
    long_text = "word " * 500  # 500 words, multiple chunks

    with patch("api.utils.summarizer.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = [{"summary_text": "Chunk summary"}]
        mock_response.raise_for_status.return_value = None

        mock_post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.post = mock_post

        events = []
        async for event in summarize_text_streaming(long_text, "Medium", "Neutral"):
            events.append(event)

        # Should have multiple chunk_start and chunk_complete pairs
        chunk_starts = [e for e in events if e["type"] == "chunk_start"]
        chunk_completes = [e for e in events if e["type"] == "chunk_complete"]

        assert len(chunk_starts) > 1
        assert len(chunk_completes) > 1
        assert len(chunk_starts) == len(chunk_completes)


@pytest.mark.asyncio
async def test_summarize_unexpected_response_format(mock_hf_token):
    """Test handling of unexpected API response format"""
    with patch("api.utils.summarizer.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = {"invalid": "format"}
        mock_response.raise_for_status.return_value = None

        mock_post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.post = mock_post

        with pytest.raises(ValueError, match="Unexpected"):
            await summarize_text_async("Test text", "Medium", "Neutral")
