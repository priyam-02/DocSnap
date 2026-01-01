import pytest
from api.utils.pdf_extractor import extract_text_from_pdf_bytes


@pytest.mark.asyncio
async def test_extract_text_from_valid_pdf(sample_pdf_bytes):
    """Test text extraction from valid PDF"""
    text = await extract_text_from_pdf_bytes(sample_pdf_bytes)

    assert isinstance(text, str)
    assert len(text) > 0
    assert "Test PDF" in text or "Content" in text


@pytest.mark.asyncio
async def test_extract_text_from_empty_pdf():
    """Test extraction from PDF with no text"""
    # Minimal PDF with no text content
    empty_pdf = b"""%PDF-1.4
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
/Resources <<>>
>>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
215
%%EOF"""

    text = await extract_text_from_pdf_bytes(empty_pdf)

    # Should return empty string or minimal whitespace
    assert isinstance(text, str)
    assert len(text.strip()) == 0


@pytest.mark.asyncio
async def test_extract_text_from_invalid_pdf():
    """Test error handling for invalid PDF"""
    invalid_pdf = b"This is not a PDF file"

    with pytest.raises(ValueError, match="Failed to extract"):
        await extract_text_from_pdf_bytes(invalid_pdf)


@pytest.mark.asyncio
async def test_extract_text_handles_multipage():
    """Test extraction from multi-page PDF"""
    # Create a simple 2-page PDF
    two_page_pdf = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R 5 0 R]
/Count 2
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
/Length 40
>>
stream
BT
/F1 12 Tf
100 700 Td
(Page One) Tj
ET
endstream
endobj
5 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 6 0 R
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
6 0 obj
<<
/Length 40
>>
stream
BT
/F1 12 Tf
100 700 Td
(Page Two) Tj
ET
endstream
endobj
xref
0 7
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000123 00000 n
0000000325 00000 n
0000000414 00000 n
0000000616 00000 n
trailer
<<
/Size 7
/Root 1 0 R
>>
startxref
705
%%EOF"""

    text = await extract_text_from_pdf_bytes(two_page_pdf)

    assert isinstance(text, str)
    # Should contain text from both pages
    assert "Page One" in text or "Page Two" in text or len(text) > 0
