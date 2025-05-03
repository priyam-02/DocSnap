import streamlit as st
import pdfplumber
from transformers import pipeline
import re


# --------- Text Extraction ---------
def extract_text_from_pdf(file):
    all_text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                all_text += page_text + "\n"
    return all_text.strip()


# --------- Format Summary into Paragraphs ---------
def format_summary_to_paragraphs(summary):
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


# --------- Load Summarization Pipeline ---------
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


# --------- Summarization Logic ---------
def summarize_text(
    text, max_chunk_size=1000, length_option="Medium", tone_option="Neutral"
):
    chunks = [text[i : i + max_chunk_size] for i in range(0, len(text), max_chunk_size)]
    summary = ""

    # Length settings
    if length_option == "Short":
        max_len = 60
        min_len = 30
    elif length_option == "Long":
        max_len = 200
        min_len = 80
    else:  # Medium
        max_len = 120
        min_len = 50

    # Refined tone instructions
    tone_instructions = {
        "Neutral": "Summarize the following content clearly and concisely:",
        "Professional": "Write a formal and professional executive summary of the following content:",
        "Casual": "Explain the following content in a friendly and easy-to-understand tone:",
    }
    instruction = tone_instructions.get(tone_option, "Summarize the following content:")

    for chunk in chunks:
        prompt = instruction + " " + chunk
        result = summarizer(
            prompt, max_length=max_len, min_length=min_len, do_sample=False
        )
        summary += result[0]["summary_text"] + " "
    return summary.strip()


# --------- Streamlit App ---------
def main():
    st.set_page_config(page_title="PDF Summarizer", page_icon="📄")
    st.title("📄 PDF Document Summarizer")

    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

    if uploaded_file is not None:
        with st.spinner("Extracting text from PDF..."):
            text = extract_text_from_pdf(uploaded_file)

        with st.expander("📄 View Extracted Text from PDF"):
            st.markdown(f"```text\n{text.strip()}\n```")

        # User chooses summary settings
        summary_length = st.selectbox(
            "✂️ Choose summary length:", ["Short", "Medium", "Long"], index=1
        )
        summary_tone = st.selectbox(
            "🎙️ Choose tone for the summary:",
            ["Neutral", "Professional", "Casual"],
            index=0,
        )

        if st.button("Summarize"):
            with st.spinner("Summarizing your document..."):
                summary = summarize_text(
                    text, length_option=summary_length, tone_option=summary_tone
                )
                st.session_state["summary"] = summary

    if "summary" in st.session_state:
        st.success("✅ Summary Generated!")
        st.markdown("### 📝 Summary")
        formatted_summary = format_summary_to_paragraphs(st.session_state["summary"])
        st.markdown(formatted_summary, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
