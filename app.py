import os
from io import BytesIO

import docx
import PyPDF2
from openai import OpenAI

# Prefer Streamlit Secrets; fall back to env var (keep what you already have for reading the key)
try:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    openai_api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_api_key)

import streamlit as st
from docx import Document

# --- Config ---
st.set_page_config(page_title="Neogen Job Advert Generator", page_icon="🧪", layout="centered")
openai.api_key = os.getenv("OPENAI_API_KEY")  # set this in Streamlit -> Settings -> Secrets

# --- Helpers ---
def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    parts = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        if txt.strip():
            parts.append(txt)
    return "\n".join(parts).strip()

def generate_neogen_advert(job_description: str) -> str:
    """
    Calls OpenAI to rewrite the job description in Neogen's house style.
    """
    prompt = f"""
You are a professional HR Copywriter working for Neogen Corporation.

Rewrite the following job description as a compelling job advert using Neogen's house style.
Keep the tone clear, professional, informative, and engaging. Do not invent details.
Always include this closing line exactly:
"Please press Apply to submit your application."

Job description:
\"\"\"{job_description}\"\"\""""
    # Chat Completions (works with OpenAI API v1-compatible libraries)
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional HR copywriter."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1200,
        temperature=0.7,
    )
    return response.choices[0].message["content"]

def text_to_docx(text: str) -> BytesIO:
    doc = Document()
    for line in text.split("\n"):
        if line.strip():
            doc.add_paragraph(line.strip())
        else:
            doc.add_paragraph()
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

# --- UI ---
st.image("assets/neogen-logo-green.webp", use_container_width=True)
st.title("📄 Neogen Job Advert Generator")
st.write("Upload a Job Description (.docx or .pdf) and generate a Neogen House Style advert.")

uploaded = st.file_uploader("Upload a Job Description file", type=["docx", "pdf"])

if uploaded:
    # Extract text
    if uploaded.name.lower().endswith(".docx"):
        jd_text = extract_text_from_docx(uploaded)
    else:
        jd_text = extract_text_from_pdf(uploaded)

    if not jd_text:
        st.warning("I couldn't extract any text from that file. If it's a scanned PDF, try a text-based PDF or DOCX.")
    else:
        st.subheader("📜 Extracted Job Description")
        st.text_area("Preview", jd_text, height=220)

        # Generate
        if st.button("✨ Generate Advert"):
            if not openai.api_key:
                st.error("OPENAI_API_KEY is not set. Add it in Streamlit → Settings → Secrets.")
            else:
                with st.spinner("Generating Neogen-style advert..."):
                    advert = generate_neogen_advert(jd_text)

                st.subheader("✅ Generated Job Advert")
                st.write(advert)

                # Download as DOCX
                out_docx = text_to_docx(advert)
                st.download_button(
                    "⬇️ Download Advert as DOCX",
                    data=out_docx,
                    file_name="neogen_job_advert.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
