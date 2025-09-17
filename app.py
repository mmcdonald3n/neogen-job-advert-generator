import os
from io import BytesIO
from zipfile import ZipFile

import streamlit as st
from docx import Document
import docx
import PyPDF2

# ── OpenAI v1 setup ──────────────────────────────────────────────────────────
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except Exception:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# ── Page setup ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Neogen Job Advert Generator", page_icon="🧪", layout="centered")
st.image("assets/neogen-logo-green.webp", use_container_width=True)
st.title("📄 Neogen Job Advert Generator")
st.caption("🔐 OpenAI API key detected." if OPENAI_API_KEY else "❌ No OpenAI API key found. Add it in Manage app → Settings → Secrets.")

MODE = st.radio("Mode", ["Single file", "Batch (multiple files)"], horizontal=True)

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

# ── Core: generate advert in Neogen house style ──────────────────────────────
HOUSE_STYLE = """
Rewrite the job description as a polished Neogen job advert in a clear, professional, concise tone.

Structure (include only sections you have content for):
- Opening paragraph (2–4 sentences) stating the role’s purpose and impact at Neogen.
- Work model / location line (e.g., onsite / hybrid / remote + city/region) if present.
- Essential Duties and Responsibilities: 6–10 crisp, action-led bullets, present tense.
- Education and Experience: 5–10 bullets covering hard requirements and strong preferences.
- Optional bullets for systems/tools (e.g., SAP/Workday/QA/SOX) and soft skills.

Rules:
- Do not invent benefits, salary, or details not present in the input.
- Keep bullets parallel and scannable (no paragraphs inside bullets).
- End with this exact closing line on its own line:
Please press Apply to submit your application.
"""

def generate_neogen_advert(job_description: str) -> str:
    prompt = f"""You are a professional HR copywriter at Neogen.

Using the HOUSE STYLE, rewrite the JOB DESCRIPTION into a Neogen-style job advert.
Do not add facts that aren't in the input. Keep it concise and scannable.

HOUSE STYLE:
\"\"\"{HOUSE_STYLE}\"\"\"

JOB DESCRIPTION:
\"\"\"{job_description}\"\"\""""

    resp = client
