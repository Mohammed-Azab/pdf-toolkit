from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pdfplumber
import pypdf

_TEXT_THRESHOLD = 10  # minimum chars on a page to count as "text"


@dataclass
class PDFInfo:
    type: Literal["text", "scanned", "mixed", "form", "encrypted"]
    page_count: int
    encryption_type: str | None
    has_forms: bool
    text_page_count: int
    image_only_page_count: int


def detect_pdf_type(path: str | Path) -> PDFInfo:
    path = str(path)
    reader = pypdf.PdfReader(path)

    if reader.is_encrypted:
        try:
            _page_count = len(reader.pages)
        except Exception:
            _page_count = 0
        return PDFInfo(
            type="encrypted",
            page_count=_page_count,
            encryption_type=_encryption_type(reader),
            has_forms=False,
            text_page_count=0,
            image_only_page_count=0,
        )

    page_count = len(reader.pages)
    has_forms = _has_forms(reader)
    text_pages = 0
    image_only_pages = 0

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if len(text.strip()) >= _TEXT_THRESHOLD:
                text_pages += 1
            elif page.images:
                image_only_pages += 1
            else:
                text_pages += 1  # blank pages count as text

    if has_forms:
        pdf_type: Literal["text", "scanned", "mixed", "form", "encrypted"] = "form"
    elif image_only_pages == 0:
        pdf_type = "text"
    elif text_pages == 0:
        pdf_type = "scanned"
    else:
        pdf_type = "mixed"

    return PDFInfo(
        type=pdf_type,
        page_count=page_count,
        encryption_type=None,
        has_forms=has_forms,
        text_page_count=text_pages,
        image_only_page_count=image_only_pages,
    )


def _has_forms(reader: pypdf.PdfReader) -> bool:
    try:
        return "/AcroForm" in reader.trailer["/Root"]
    except (KeyError, TypeError):
        return False


def _encryption_type(reader: pypdf.PdfReader) -> str:
    try:
        enc_ref = reader.trailer.get("/Encrypt")
        if enc_ref is None:
            return "unknown"
        enc = enc_ref.get_object() if hasattr(enc_ref, "get_object") else enc_ref
        v = enc.get("/V", 0)
        if v >= 5:
            return "AES-256"
        if v == 4:
            return "AES-128"
        if v == 2:
            return "RC4-128"
        return f"RC4-40 (V={v})"
    except Exception:
        return "unknown"
