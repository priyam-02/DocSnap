import streamlit as st
import pdfplumber
from transformers import pipeline


def extract_text_from_pdf(file):
    all_text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                all_text += page_text + "\n"
    return all_text.strip()


# Load the summarization model
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")


def summarize_text(text, max_chunk_size=1000):
    # Step 1: Break the text into chunks
    chunks = [text[i : i + max_chunk_size] for i in range(0, len(text), max_chunk_size)]

    summary = ""

    # Step 2: Run summarization on each chunk
    for chunk in chunks:
        result = summarizer(chunk, max_length=150, min_length=40, do_sample=False)
        summary += result[0]["summary_text"] + " "

    return summary.strip()
