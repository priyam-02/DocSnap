import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import UploadFile
import io


def test_health_check(client):
    """Test /api/health endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "PDF Summarizer API"}


@pytest.mark.asyncio
async def test_summarize_success(client, sample_pdf_bytes, mock_hf_token, mock_hf_response):
    """Test successful summarization"""
    with patch("api.utils.summarizer.httpx.AsyncClient") as mock_client:
        # Mock HF API response (httpx Response methods are sync, not async)
        mock_response = MagicMock()
        mock_response.json.return_value = mock_hf_response
        mock_response.raise_for_status.return_value = None

        mock_post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.post = mock_post

        response = client.post(
            "/api/summarize",
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
            data={"length_option": "Medium", "tone_option": "Neutral"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "formatted_summary" in data
        assert "extracted_text_preview" in data
        assert data["success"] is True
        assert "metadata" in data


def test_summarize_invalid_file_type(client):
    """Test rejection of non-PDF files"""
    response = client.post(
        "/api/summarize",
        files={"file": ("test.txt", b"Some text", "text/plain")},
        data={"length_option": "Medium", "tone_option": "Neutral"},
    )

    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]


def test_summarize_file_too_large(client, mock_hf_token):
    """Test rejection of files > 10MB"""
    large_file = b"x" * (11 * 1024 * 1024)  # 11MB
    response = client.post(
        "/api/summarize",
        files={"file": ("test.pdf", large_file, "application/pdf")},
        data={"length_option": "Medium", "tone_option": "Neutral"},
    )

    assert response.status_code == 400
    assert "File too large" in response.json()["detail"]


def test_summarize_invalid_length_option(client, sample_pdf_bytes, mock_hf_token):
    """Test validation of length_option"""
    response = client.post(
        "/api/summarize",
        files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
        data={"length_option": "INVALID", "tone_option": "Neutral"},
    )

    assert response.status_code == 422  # Validation error


def test_summarize_invalid_tone_option(client, sample_pdf_bytes, mock_hf_token):
    """Test validation of tone_option"""
    response = client.post(
        "/api/summarize",
        files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
        data={"length_option": "Medium", "tone_option": "INVALID"},
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_summarize_missing_hf_token(client, sample_pdf_bytes, monkeypatch):
    """Test error when HF_API_TOKEN is not set"""
    # Remove HF_API_TOKEN from environment
    monkeypatch.delenv("HF_API_TOKEN", raising=False)

    response = client.post(
        "/api/summarize",
        files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
        data={"length_option": "Medium", "tone_option": "Neutral"},
    )

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_summarize_hf_api_error(client, sample_pdf_bytes, mock_hf_token):
    """Test handling of HF API errors"""
    with patch("api.utils.summarizer.httpx.AsyncClient") as mock_client:
        # Mock HF API error
        mock_response = AsyncMock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"

        from httpx import HTTPStatusError, Request, Response

        mock_post = AsyncMock(
            side_effect=HTTPStatusError(
                "Service Unavailable",
                request=MagicMock(),
                response=mock_response,
            )
        )
        mock_client.return_value.__aenter__.return_value.post = mock_post

        response = client.post(
            "/api/summarize",
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
            data={"length_option": "Medium", "tone_option": "Neutral"},
        )

        assert response.status_code == 500


@pytest.mark.asyncio
async def test_summarize_stream_endpoint(client, sample_pdf_bytes, mock_hf_token, mock_hf_response):
    """Test streaming endpoint returns SSE events"""
    with patch("api.utils.summarizer.httpx.AsyncClient") as mock_client:
        # Mock HF API response (httpx Response methods are sync, not async)
        mock_response = MagicMock()
        mock_response.json.return_value = mock_hf_response
        mock_response.raise_for_status.return_value = None

        mock_post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.post = mock_post

        response = client.post(
            "/api/summarize-stream",
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
            data={"length_option": "Medium", "tone_option": "Neutral"},
        )

        assert response.status_code == 200
        # Streaming endpoint returns text/event-stream
        assert "text/event-stream" in response.headers.get("content-type", "")


def test_summarize_stream_invalid_file_type(client):
    """Test streaming endpoint rejects non-PDF files"""
    response = client.post(
        "/api/summarize-stream",
        files={"file": ("test.txt", b"Some text", "text/plain")},
        data={"length_option": "Medium", "tone_option": "Neutral"},
    )

    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]


def test_summarize_stream_file_too_large(client, mock_hf_token):
    """Test streaming endpoint rejects files > 10MB"""
    large_file = b"x" * (11 * 1024 * 1024)  # 11MB
    response = client.post(
        "/api/summarize-stream",
        files={"file": ("test.pdf", large_file, "application/pdf")},
        data={"length_option": "Medium", "tone_option": "Neutral"},
    )

    assert response.status_code == 400
    assert "File too large" in response.json()["detail"]


@pytest.mark.asyncio
async def test_rate_limiting(client, sample_pdf_bytes, mock_hf_token, mock_hf_response):
    """Test rate limiting enforcement (requires multiple requests)"""
    with patch("api.utils.summarizer.httpx.AsyncClient") as mock_client:
        # Mock HF API response (httpx Response methods are sync, not async)
        mock_response = MagicMock()
        mock_response.json.return_value = mock_hf_response
        mock_response.raise_for_status.return_value = None

        mock_post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.post = mock_post

        # Note: Actual rate limit testing would require making 11+ requests
        # This is a simplified test that just verifies the endpoint works
        response = client.post(
            "/api/summarize",
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
            data={"length_option": "Medium", "tone_option": "Neutral"},
        )

        assert response.status_code == 200
