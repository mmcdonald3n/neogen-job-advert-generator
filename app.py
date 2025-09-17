import os
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
def extract_text_from_docx(file)_
