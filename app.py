import os
from io import BytesIO

import streamlit as st
from docx import Document
import docx
import PyPDF2

# ─────────────────────────────────────────────────────────────────────────────
# OpenAI (v1) setup
# ─────────────────────────────────────────────────────────────────────────────
# Prefer Streamlit Secrets; fall back to environment variable
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except Exception:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# ─────────────────────────────────────────────────────────────────────────────
# Streamlit page
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Neogen Job Advert Generator", page_icon="🧪", layout="centered")
st.image("assets/neogen-logo-green.webp", use_container_width=True)

st.title("📄 Neogen Job Advert Generator")
st.write("Upload a Job Description (.docx or .pdf) and generate a Neogen House Style advert.")

# Small status line so you know the key is loaded (does not reveal it)
st.caption("🔐 OpenAI API key detected." if OPENAI_API_KEY else "❌ No OpenAI API key found. Add it in Settings → Secrets.")

# ─────────────────────────────────────────────────────────────────────────────
# Helpers: extract text
# ─────────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────────
# Core: generate advert in Neogen house style
# ─────────────────────────────────────────────────────────────────────────────
def generate_neogen_advert(job_description: str) -> str:
    house_style = """
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

    prompt = f"""You are a professional HR copywriter at Neogen.

Using the HOUSE STYLE, rewrite the JOB DESCRIPTION into a Neogen-style job advert.
Do not add facts that aren't in the input. Keep it concise and scannable.

HOUSE STYLE:
\"\"\"{house_style}\"\"\"

JOB DESCRIPTION:
\"\"\"{job_description}\"\"\""""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",             # change to "gpt-4o" if you prefer
        messages=[
            {"role": "system", "content": "You are a precise HR copywriter who follows style guides faithfully."},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=1200,
        temperature=0.4,                 # lower = tighter adherence to style
    )
    return resp.choices[0].message.content

# ─────────────────────────────────────────────────────────────────────────────
# Utility: build a DOCX for download
# ─────────────────────────────────────────────────────────────────────────────
def to_docx(text: str) -> BytesIO:
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

# ─────────────────────────────────────────────────────────────────────────────
# UI: upload + run
# ─────────────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader("Upload a Job Description file", type=["docx", "pdf"])

if uploaded:
    filename = uploaded.name.lower()
    if filename.endswith(".docx"):
        jd_text = extract_text_from_docx(uploaded)
    else:
        jd_text = extract_text_from_pdf(uploaded)

    if not jd_text:
        st.warning("I couldn't extract any text. If it's a scanned PDF, try exporting a text-based PDF or DOCX.")
    else:
        st.subheader("📜 Extracted Job Description")
        st.text_area("Preview", jd_text, height=220)

        if st.button("✨ Generate Advert"):
            if not OPENAI_API_KEY:
                st.error("OPENAI_API_KEY is not set. Add it in Manage app → Settings → Secrets.")
            else:
                with st.spinner("Generating Neogen-style advert..."):
                    advert = generate_neogen_advert(jd_text)

                st.subheader("✅ Generated Job Advert")
                st.write(advert)

                # Download as DOCX
                out = to_docx(advert)
                st.download_button(
                    "⬇️ Download Advert as DOCX",
                    data=out,
                    file_name="neogen_job_advert.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
