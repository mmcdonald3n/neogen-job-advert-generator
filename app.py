
import streamlit as st
import docx
import openai
import os
import PyPDF2
from io import BytesIO
from docx import Document

# Load OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- Extract text from .docx ---
def extract_text_from_docx(file):
    doc = docx.Document(file)
    return '\n'.join([para.text for para in doc.paragraphs if para.text.strip() != ""])

# --- Extract text from .pdf ---
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ''
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + '\n'
    return text.strip()

# --- Generate job advert using OpenAI ---
def generate_neogen_advert(job_description):
    prompt = f"""
You are a professional HR Copywriter working for Neogen Corporation.

Rewrite the following job description as a compelling job advert using Neogen's house style. 
Keep the tone clear, professional, informative, and engaging. Do not make up any details.
Always include a closing line: “Please press Apply to submit your application.”

Here is the job description:
"""
{job_description}
"""
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional HR copywriter."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1200,
        temperature=0.7
    )

    return response.choices[0].message['content']

# --- Convert advert text to .docx ---
def text_to_docx(text):
    doc = Document()
    for paragraph in text.split('\n'):
        if paragraph.strip():
            doc.add_paragraph(paragraph.strip())
    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output

# --- Streamlit UI ---
st.set_page_config(page_title="Neogen Job Advert Generator", page_icon="🧪", layout="centered")

# Display logo at top
st.image("assets/neogen-logo-green.webp", use_column_width=True)

st.title("📄 Neogen Job Advert Generator")
st.write("Upload a Job Description (.docx or .pdf) and generate a Neogen House Style advert instantly.")

uploaded_file = st.file_uploader("Upload a Job Description", type=["docx", "pdf"])

if uploaded_file:
    if uploaded_file.name.lower().endswith(".docx"):
        jd_text = extract_text_from_docx(uploaded_file)
    elif uploaded_file.name.lower().endswith(".pdf"):
        jd_text = extract_text_from_pdf(uploaded_file)
    else:
        st.error("Please upload a .docx or .pdf file only.")
        jd_text = None

    if jd_text:
        st.subheader("📜 Extracted Job Description")
        st.text_area("Preview", jd_text, height=200)

        if st.button("✨ Generate Advert"):
            with st.spinner("Generating Neogen-style advert..."):
                advert_text = generate_neogen_advert(jd_text)

            st.subheader("✅ Generated Job Advert")
            st.write(advert_text)

            # Download as DOCX
            docx_file = text_to_docx(advert_text)
            st.download_button(
                label="⬇️ Download Advert as DOCX",
                data=docx_file,
                file_name="neogen_job_advert.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
