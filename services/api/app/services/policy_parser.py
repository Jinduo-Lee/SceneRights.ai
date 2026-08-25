import io
from pathlib import Path
from typing import Tuple
from pypdf import PdfReader
from docx import Document

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def validate_policy_file(filename: str, content_length: int) -> Tuple[bool, str]:
    """Validates file size and extension server-side."""
    if content_length > MAX_FILE_SIZE_BYTES:
        return False, f"File size ({content_length} bytes) exceeds maximum allowed limit of 10MB."

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file format '{ext}'. Allowed formats: TXT, Markdown, PDF, DOCX."

    return True, ""


def parse_policy_document(filename: str, content: bytes) -> str:
    """Deterministically extracts raw document text from supported policy formats."""
    valid, err_msg = validate_policy_file(filename, len(content))
    if not valid:
        raise ValueError(err_msg)

    ext = Path(filename).suffix.lower()

    if ext in (".txt", ".md"):
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback decoding
            return content.decode("latin-1")

    elif ext == ".pdf":
        reader = PdfReader(io.BytesIO(content))
        text_parts = []
        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        extracted = "\n\n".join(text_parts).strip()
        if not extracted:
            raise ValueError("PDF contains no extractable text. Scanned or image-only PDFs are unsupported.")
        return extracted

    elif ext == ".docx":
        doc = Document(io.BytesIO(content))
        text_parts = [p.text for p in doc.paragraphs if p.text.strip()]
        extracted = "\n".join(text_parts).strip()
        if not extracted:
            raise ValueError("DOCX document contains no readable text content.")
        return extracted

    else:
        raise ValueError(f"Unsupported file format: '{ext}'")

