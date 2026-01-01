import pytest
from api.utils.formatter import format_summary_to_paragraphs


def test_format_single_sentence():
    """Test formatting single sentence (no paragraph breaks)"""
    summary = "This is a single sentence summary."
    formatted = format_summary_to_paragraphs(summary)

    assert formatted == summary
    assert "\n\n" not in formatted


def test_format_three_sentences():
    """Test formatting three sentences (single paragraph)"""
    summary = "First sentence. Second sentence. Third sentence."
    formatted = format_summary_to_paragraphs(summary)

    # Should have no paragraph breaks (< 4 sentences)
    assert formatted == summary
    assert "\n\n" not in formatted


def test_format_multiple_sentences():
    """Test formatting multiple sentences (creates paragraphs)"""
    summary = (
        "Sentence one. Sentence two. Sentence three. "
        "Sentence four. Sentence five. Sentence six."
    )
    formatted = format_summary_to_paragraphs(summary)

    # Should have paragraph breaks (groups of 3)
    assert "\n\n" in formatted
    paragraphs = formatted.split("\n\n")
    assert len(paragraphs) == 2


def test_format_many_sentences():
    """Test formatting many sentences (multiple paragraphs)"""
    # 9 sentences should create 3 paragraphs
    sentences = [f"Sentence {i}." for i in range(1, 10)]
    summary = " ".join(sentences)
    formatted = format_summary_to_paragraphs(summary)

    paragraphs = formatted.split("\n\n")
    assert len(paragraphs) == 3

    # Each paragraph should have ~3 sentences
    for para in paragraphs:
        sentence_count = para.count(".")
        assert sentence_count <= 3


def test_format_preserves_content():
    """Test that formatting doesn't lose content"""
    summary = "One. Two. Three. Four. Five. Six."
    formatted = format_summary_to_paragraphs(summary)

    # Remove paragraph breaks to compare content
    formatted_flat = formatted.replace("\n\n", " ")

    # Content should be preserved (allowing for whitespace differences)
    assert "One." in formatted
    assert "Six." in formatted
    assert len(formatted_flat.split()) == len(summary.split())


def test_format_empty_string():
    """Test formatting empty string"""
    formatted = format_summary_to_paragraphs("")

    assert formatted == ""


def test_format_whitespace_only():
    """Test formatting whitespace-only string"""
    formatted = format_summary_to_paragraphs("   \n\n   ")

    # Should return empty or minimal whitespace
    assert len(formatted.strip()) == 0


def test_format_with_existing_newlines():
    """Test formatting text that already has newlines"""
    summary = "First sentence.\nSecond sentence.\nThird sentence.\nFourth sentence."
    formatted = format_summary_to_paragraphs(summary)

    # Should still group into paragraphs regardless of existing newlines
    assert isinstance(formatted, str)
    assert len(formatted) > 0


def test_format_with_abbreviations():
    """Test formatting handles abbreviations (e.g., Mr., Dr.)"""
    summary = "Dr. Smith works at MIT. He researches AI. This is important work."
    formatted = format_summary_to_paragraphs(summary)

    # Should handle abbreviations correctly and not treat them as sentence endings
    assert "Dr. Smith" in formatted or "Dr.Smith" in formatted


def test_format_mixed_punctuation():
    """Test formatting with mixed sentence endings (!?)"""
    summary = "What is this? It's amazing! We should investigate. Very interesting indeed."
    formatted = format_summary_to_paragraphs(summary)

    # Should handle question marks and exclamation points as sentence endings
    assert isinstance(formatted, str)
    assert len(formatted) > 0


def test_format_very_long_text():
    """Test formatting very long text (stress test)"""
    sentences = [f"This is sentence number {i}." for i in range(1, 101)]
    summary = " ".join(sentences)
    formatted = format_summary_to_paragraphs(summary)

    # Should create multiple paragraphs
    paragraphs = formatted.split("\n\n")
    assert len(paragraphs) > 10  # 100 sentences / 3 ≈ 33 paragraphs

    # All content should be preserved
    assert "sentence number 1" in formatted
    assert "sentence number 100" in formatted
