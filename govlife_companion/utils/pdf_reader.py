from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader


def extract_pdf_text(uploaded_file) -> str:
    if not uploaded_file:
        return ""
    data = uploaded_file.read()
    reader = PdfReader(BytesIO(data))
    text = []
    for page in reader.pages:
        text.append(page.extract_text() or "")
    return "\n".join(text).strip()

