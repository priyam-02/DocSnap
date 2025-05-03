# 📄 PDF Document Summarizer

This is a Streamlit web app that allows users to upload a PDF document and generate a concise, human-readable summary. Users can customize the **length** and **tone** of the summary using intuitive dropdown controls.

## 🎥 Demo

## ✨ Features

- 🔹 Upload any PDF document
- ✂️ Choose summary length: Short, Medium, or Long
- 🎙️ Choose tone: Neutral, Professional, or Casual
- 📑 Automatically formats the summary into readable paragraphs

## 🛠 Tech Stack

- Python
- Streamlit
- Transformers (`facebook/bart-large-cnn`)
- pdfplumber
- PyTorch

## 🚀 How to Run

1. **Clone the repo:**

   ```bash
   git clone https://github.com/yourusername/document-summarizer.git
   cd document-summarizer
   ```

2. **(Optional) Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app:**
   ```bash
   streamlit run app.py
   ```
