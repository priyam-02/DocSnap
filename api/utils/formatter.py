import re


def format_summary_to_paragraphs(summary):
    """
    Format summary into paragraphs by grouping sentences.
    Groups every 3 sentences into a paragraph.

    Direct copy from app.py lines 19-30
    """
    sentences = re.split(r"(?<=[.?!])\s+(?=[A-Z])", summary.strip())
    paragraphs = []
    temp = []
    for i, sentence in enumerate(sentences, 1):
        temp.append(sentence)
        if i % 3 == 0:
            paragraphs.append(" ".join(temp))
            temp = []
    if temp:
        paragraphs.append(" ".join(temp))
    return "\n\n".join(paragraphs)
