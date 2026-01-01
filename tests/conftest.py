import os
import pytest
from fastapi.testclient import TestClient
from api.summarize import app


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_hf_token(monkeypatch):
    """Mock HF API token"""
    monkeypatch.setenv("HF_API_TOKEN", "test_token_123")


@pytest.fixture
def sample_pdf_bytes():
    """Load sample PDF for testing"""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "sample.pdf")

    # If sample.pdf doesn't exist, create a minimal valid PDF
    if not os.path.exists(fixture_path):
        # Minimal valid PDF with text "Test PDF"
        minimal_pdf = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF Content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF"""
        os.makedirs(os.path.dirname(fixture_path), exist_ok=True)
        with open(fixture_path, "wb") as f:
            f.write(minimal_pdf)

    with open(fixture_path, "rb") as f:
        return f.read()


@pytest.fixture
def mock_hf_response():
    """Mock successful HF API response"""
    return [{"summary_text": "This is a test summary."}]


@pytest.fixture
def mock_hf_streaming_response():
    """Mock successful HF API streaming response for multiple chunks"""
    return [
        {"summary_text": "This is the first chunk summary."},
        {"summary_text": "This is the second chunk summary."},
    ]
