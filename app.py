from docx.enum.style import WD_STYLE_TYPE

def to_docx_structured(text: str) -> BytesIO:
    """
    Build a DOCX with Neogen-style formatting:
    - Known section headers are bold.
    - Lines beginning with '- ' (or '• ') become bullets.
    - Fallback to a visible '• ' if the 'List Bullet' style isn't available.
    """
    doc = Document()

    # Ensure a bullet style exists; if not, we’ll catch KeyError later and fallback
    bullet_style_name = "List Bullet"
    if bullet_style_name not in [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]:
        # leave as-is; python-docx default usually has it, but we’ll handle absence
        pass

    def add_header(line: str) -> bool:
        """Return True if a header was added."""
        norm = line.strip()
        # case-insensitive startswith against our list
        for hdr in SECTION_HEADERS:
            if norm.lower().startswith(hdr.lower()):
                p = doc.add_paragraph()
                # split "Header: tail" if present
                if hdr.endswith(":"):
                    hdr_core = hdr
                else:
                    hdr_core = hdr + (":" if norm[len(hdr):].lstrip().startswith(":") else "")
                # write bold header
                run = p.add_run(hdr_core)
                run.bold = True
                # any trailing text after the header token (e.g., "Location: Hybrid – EMEAI")
                tail = norm[len(hdr):].lstrip()
                if tail.startswith(":"):
                    tail = tail[1:].lstrip()
                if tail:
                    p.add_run(" " + tail)
                return True
        return False

    lines = [ln.rstrip() for ln in text.split("\n")]
    for raw in lines:
        line = raw.strip()
        if not line:
            doc.add_paragraph()
            continue

        # Header?
        if add_header(line):
            continue

        # Bullet?
        if line.startswith("- ") or line.startswith("• "):
            bullet_text = line[2:].strip()
            try:
                # true list bullet
                doc.add_paragraph(bullet_text, style=bullet_style_name)
            except KeyError:
                # fallback: visible bullet glyph (not a numbered list)
                p = doc.add_paragraph()
                p.add_run("• ").bold = True
                p.add_run(bullet_text)
            continue

        # Default paragraph
        doc.add_paragraph(line)

    out = BytesIO()
    doc.save
