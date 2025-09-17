import os
import re
from io import BytesIO
from zipfile import ZipFile

import streamlit as st
from docx import Document
import docx
import PyPDF2

# ── Page setup ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Neogen Job Advert Generator", page_icon="🧪", layout="centered")
st.image("assets/neogen-logo-green.webp", use_container_width=True)
st.title("📄 Neogen Job Advert Generator")

# Prefer Streamlit Secrets; fall back to env var (don’t build client yet)
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except Exception:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.caption("🔐 OpenAI API key detected." if OPENAI_API_KEY else "❌ No OpenAI API key found. Add it in Manage app → Settings → Secrets.")

# ── Helpers: extract text ────────────────────────────────────────────────────
def extract_text_from_docx(file) -> str:
    d = docx.Document(file)
    return "\n".join(p.text for p in d.paragraphs if p.text.strip())

def extract_text_from_pdf(file) -> str:
    reader = PyPDF2.PdfReader(file)
    parts = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        if txt.strip():
            parts.append(txt)
    return "\n".join(parts).strip()

# ── Helpers: sanitise output (remove Markdown) ───────────────────────────────
def strip_markdown(s: str) -> str:
    # bold/italic/code
    s = re.sub(r"\*\*(.*?)\*\*", r"\1", s)
    s = re.sub(r"\*(.*?)\*", r"\1", s)
    s = re.sub(r"`(.*?)`", r"\1", s)
    # headings like "## Title"
    s = re.sub(r"^\s{0,3}#{1,6}\s*", "", s, flags=re.MULTILINE)
    # bullet symbol normalisation
    s = s.replace("•", "-").replace("–", "-").replace("—", "-")
    # normalise whitespace
    s = re.sub(r"\r\n", "\n", s)
    return s.strip()

# ── Ho
