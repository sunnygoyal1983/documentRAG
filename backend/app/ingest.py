import os
from typing import List
import re
import tempfile
import subprocess
import uuid


def extract_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".txt":
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
            # If the file contains literal "\n" sequences (common in copied samples),
            # convert them into actual newlines for better chunking and retrieval.
            if "\\n" in text and "\n" not in text:
                text = text.replace("\\n", "\n")
            return text
    elif ext == ".pdf":
        text = ""
        pypdf_err = None
        used_ocr = False
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(path)

            # Handle encrypted PDFs explicitly
            if getattr(reader, "is_encrypted", False):
                try:
                    # attempt empty password (common)
                    reader.decrypt("")
                except Exception:
                    raise RuntimeError("PDF is encrypted/password-protected and cannot be processed")

            pages = [p.extract_text() or "" for p in reader.pages]
            text = "\n\n".join(pages).strip()
        except Exception as e:
            pypdf_err = e
            text = ""

        # Fallback: pdfplumber (pdfminer) often extracts text from PDFs where PyPDF2 fails.
        if len(text) < 20:
            try:
                import pdfplumber
                with pdfplumber.open(path) as pdf:
                    parts = []
                    for page in pdf.pages:
                        parts.append((page.extract_text() or "").strip())
                text2 = "\n\n".join([p for p in parts if p]).strip()
                if text2:
                    return text2
            except Exception as e:
                # If both fail, return the most informative error
                if pypdf_err is not None:
                    # Before failing, try OCR if enabled
                    text_ocr = _maybe_ocr_pdf(path)
                    if text_ocr:
                        return text_ocr
                    raise RuntimeError(f"PDF text extraction failed (PyPDF2: {pypdf_err}; pdfplumber: {e})")
                raise RuntimeError(f"PDF text extraction failed (pdfplumber: {e})")

        # If we got here with short text, last resort OCR (for image-based or weird-encoding PDFs)
        if len(text) < 20:
            text_ocr = _maybe_ocr_pdf(path)
            if text_ocr:
                return text_ocr
        return text
    elif ext == ".docx":
        try:
            import docx
        except Exception:
            raise RuntimeError("python-docx is required for DOCX extraction")
        doc = docx.Document(path)
        paras = [p.text for p in doc.paragraphs]
        return "\n\n".join(paras)
    else:
        return ""


def chunk_text(text: str, max_chars: int = 1600, overlap_chars: int = 250) -> List[str]:
    """
    Chunk text in a more RAG-friendly way than naive whitespace token windows:
    - Normalize whitespace
    - Split into paragraphs (keeps headings/sections together better)
    - Pack paragraphs into ~max_chars windows with character overlap

    This is simple, dependency-free, and behaves much better on PDFs/DOCX.
    """
    if not text:
        return []

    t = text.replace("\r", "")
    # normalize whitespace but keep paragraph breaks
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    if not t:
        return []

    paras = [p.strip() for p in t.split("\n\n") if p.strip()]
    chunks: List[str] = []
    cur: List[str] = []
    cur_len = 0

    def flush():
        nonlocal cur, cur_len
        if not cur:
            return
        chunk = "\n\n".join(cur).strip()
        if chunk:
            chunks.append(chunk)
        cur = []
        cur_len = 0

    for p in paras:
        # If a single paragraph is huge, hard-split it.
        if len(p) > max_chars:
            flush()
            start = 0
            while start < len(p):
                end = min(len(p), start + max_chars)
                chunks.append(p[start:end].strip())
                start = max(0, end - overlap_chars)
            continue

        # Pack paragraphs into a window.
        add_len = len(p) + (2 if cur else 0)
        if cur_len + add_len > max_chars:
            flush()
        cur.append(p)
        cur_len += add_len

    flush()

    # Apply overlap between chunks (character overlap) to preserve continuity.
    if overlap_chars > 0 and len(chunks) > 1:
        overlapped: List[str] = []
        prev_tail = ""
        for i, ch in enumerate(chunks):
            if i == 0:
                overlapped.append(ch)
            else:
                prev_tail = chunks[i - 1][-overlap_chars:]
                overlapped.append((prev_tail + "\n\n" + ch).strip())
        chunks = overlapped

    return chunks


def _maybe_ocr_pdf(path: str) -> str:
    """
    Optional OCR for PDFs. Enabled by env ENABLE_OCR=1.
    Uses ocrmypdf (Tesseract) to create a text-layer PDF, then extracts text via pdfplumber.
    """
    enable = os.environ.get("ENABLE_OCR", "0").strip().lower() in {"1", "true", "yes", "on"}
    if not enable:
        return ""

    lang = os.environ.get("OCR_LANG", "eng").strip().strip('"').strip("'") or "eng"
    timeout_s = int(os.environ.get("OCR_TIMEOUT_S", "600"))
    max_pages = int(os.environ.get("OCR_MAX_PAGES", "0"))  # 0 = no limit

    try:
        import ocrmypdf  # noqa: F401
    except Exception:
        # ocrmypdf not installed
        return ""

    # Create a temp output PDF
    tmp_dir = tempfile.gettempdir()
    out_path = os.path.join(tmp_dir, f"ocr_{uuid.uuid4().hex}.pdf")

    try:
        # We call the CLI to keep behavior consistent and avoid API differences.
        cmd = [
            "ocrmypdf",
            "--skip-text",
            "--force-ocr",
            "--output-type",
            "pdf",
            "--language",
            lang,
        ]
        if max_pages > 0:
            cmd += ["--pages", f"1-{max_pages}"]
        cmd += [path, out_path]

        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_s)

        # Extract text from OCR'd PDF
        import pdfplumber
        with pdfplumber.open(out_path) as pdf:
            parts = []
            for page in pdf.pages:
                parts.append((page.extract_text() or "").strip())
        return "\n\n".join([p for p in parts if p]).strip()
    except Exception:
        return ""
    finally:
        try:
            if os.path.exists(out_path):
                os.remove(out_path)
        except Exception:
            pass
