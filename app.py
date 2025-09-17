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

# ── OpenAI generator (client created lazily) ─────────────────────────────────
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
    from openai import OpenAI  # lazy import so UI always renders
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""You are a professional HR copywriter at Neogen.

Using the HOUSE STYLE, rewrite the JOB DESCRIPTION into a Neogen-style job advert.
Do not add facts that aren't in the input. Keep it concise and scannable.

HOUSE STYLE:
\"\"\"{HOUSE_STYLE}\"\"\"

JOB DESCRIPTION:
\"\"\"{job_description}\"\"\""""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",  # change to "gpt-4o" for highest quality if desired
        messages=[
            {"role": "system", "content": "You are a precise HR copywriter who follows style guides faithfully."},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=1200,
        temperature=0.4,
    )
    return resp.choices[0].message.content

# ── Utility: build a DOCX for download ───────────────────────────────────────
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

# ── UI: tabs (robust render) ─────────────────────────────────────────────────
tab_single, tab_batch = st.tabs(["Single file", "Batch (multiple files)"])

with tab_single:
    uploaded = st.file_uploader(
        "Upload a Job Description (.docx or .pdf)",
        type=["docx", "pdf"],
        key="single_uploader"
    )

    if uploaded:
        try:
            jd_text = extract_text_from_docx(uploaded) if uploaded.name.lower().endswith(".docx") \
                      else extract_text_from_pdf(uploaded)
        except Exception as e:
            st.error(f"Couldn't read the file: {e}")
            jd_text = ""

        if not jd_text:
            st.warning("I couldn't extract any text. If it's a scanned PDF, try exporting a text-based PDF or DOCX.")
        else:
            st.subheader("📜 Extracted Job Description")
            st.text_area("Preview", jd_text, height=220, key="single_preview")

            if st.button("✨ Generate Advert", key="single_generate"):
                if not OPENAI_API_KEY:
                    st.error("OPENAI_API_KEY is not set. Add it in Manage app → Settings → Secrets.")
                else:
                    with st.spinner("Generating Neogen-style advert..."):
                        try:
                            advert = generate_neogen_advert(jd_text)
                        except Exception as e:
                            st.error(f"Generation failed: {e}")
                            advert = ""

                    if advert:
                        st.subheader("✅ Generated Job Advert")
                        st.code(advert)  # copy-to-clipboard icon
                        edited = st.text_area("Edit before download (optional)", advert, height=260, key="single_edit")
                        use_text = edited if edited.strip() else advert

                        out_bytes = to_docx(use_text)  # do NOT st.write(out_bytes)
                        st.download_button(
                            "⬇️ Download Advert as DOCX",
                            data=out_bytes,
                            file_name="neogen_job_advert.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="single_download",
                        )

with tab_batch:
    files = st.file_uploader(
        "Upload multiple Job Descriptions (.docx or .pdf)",
        type=["docx", "pdf"],
        accept_multiple_files=True,
        key="batch_uploader",
    )
    st.caption("Tip: drag several files at once. You’ll get a ZIP of DOCX adverts.")

    if files and st.button("✨ Generate Adverts (Batch)", key="batch_generate"):
        if not OPENAI_API_KEY:
            st.error("OPENAI_API_KEY is not set. Add it in Manage app → Settings → Secrets.")
        else:
            zip_buf = BytesIO()
            try:
                with ZipFile(zip_buf, "w") as z:
                    for f in files:
                        try:
                            jd_text = extract_text_from_docx(f) if f.name.lower().endswith(".docx") \
                                      else extract_text_from_pdf(f)
                            if not jd_text:
                                continue
                            advert = generate_neogen_advert(jd_text)
                            docx_bytes = to_docx(advert).getvalue()
                            base = os.path.splitext(os.path.basename(f.name))[0]
                            z.writestr(f"{base}_neogen_advert.docx", docx_bytes)
                        except Exception as e:
                            base = os.path.splitext(os.path.basename(f.name))[0]
                            z.writestr(f"{base}_ERROR.txt", f"Failed to process {f.name}:\n{e}")
                zip_buf.seek(0)
                st.success("Batch complete.")
                st.download_button(
                    "⬇️ Download ZIP of adverts",
                    data=zip_buf,
                    file_name="neogen_job_adverts.zip",
                    mime="application/zip",
                    key="batch_download",
                )
            except Exception as e:
                st.error(f"Batch failed: {e}")
