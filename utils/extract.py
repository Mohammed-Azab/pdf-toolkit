from __future__ import annotations

import csv
import os
import shutil
import subprocess
from pathlib import Path

import pdfplumber
import pypdf
from tqdm import tqdm

from utils import atomic_write, parse_pages
from utils.pdf_info import detect_pdf_type

_VALID_TYPES = {"text", "images", "tables", "pages"}


def extract(
    input_path: str | Path,
    output_path: str | Path,
    type_: str = "text",
    pages: str = "all",
    dry_run: bool = False,
) -> None:
    input_path, output_path = str(input_path), str(output_path)

    if type_ not in _VALID_TYPES:
        raise ValueError(
            f"Invalid type '{type_}'. Choose from: {sorted(_VALID_TYPES)}"
        )

    info = detect_pdf_type(input_path)
    if info.type == "encrypted":
        raise RuntimeError(f"{input_path} is encrypted. Unlock it first.")

    reader = pypdf.PdfReader(input_path)
    page_indices = parse_pages(pages, len(reader.pages))

    if dry_run:
        print(
            f"[dry-run] Would extract {type_} from "
            f"{len(page_indices)} page(s) → {output_path}"
        )
        return

    if type_ == "text":
        _extract_text(input_path, output_path, page_indices, info)
    elif type_ == "images":
        _extract_images(input_path, output_path, page_indices, reader)
    elif type_ == "tables":
        _extract_tables(input_path, output_path, page_indices)
    elif type_ == "pages":
        _extract_pages(input_path, output_path, page_indices)


def _extract_text(
    input_path: str, output_path: str, page_indices: list[int], info
) -> None:
    if info.type in ("scanned", "mixed"):
        print(
            "Warning: scanned PDF detected. "
            "Falling back to OCR (requires tesseract + pdf2image)."
        )
        _ocr_text(input_path, output_path, page_indices)
        return

    lines: list[str] = []
    with pdfplumber.open(input_path) as pdf:
        for i in tqdm(page_indices, desc="Extracting text", unit="page"):
            text = pdf.pages[i].extract_text() or ""
            lines.append(f"--- Page {i + 1} ---\n{text}\n")

    def _write(tmp: str) -> None:
        Path(tmp).write_text("\n".join(lines), encoding="utf-8")

    atomic_write(output_path, _write)
    print(f"Extracted text from {len(page_indices)} page(s) → {output_path}")


def _ocr_text(
    input_path: str, output_path: str, page_indices: list[int]
) -> None:
    if not shutil.which("tesseract"):
        raise RuntimeError(
            "tesseract not found.\n"
            "Install:  apt: tesseract-ocr | brew: tesseract | choco: tesseract"
        )
    from pdf2image import convert_from_path
    import pytesseract

    images = convert_from_path(input_path)
    lines: list[str] = []
    for i in tqdm(page_indices, desc="OCR", unit="page"):
        text = pytesseract.image_to_string(images[i])
        lines.append(f"--- Page {i + 1} (OCR) ---\n{text}\n")

    def _write(tmp: str) -> None:
        Path(tmp).write_text("\n".join(lines), encoding="utf-8")

    atomic_write(output_path, _write)
    print(f"OCR extracted {len(page_indices)} page(s) → {output_path}")


def _extract_images(
    input_path: str, output_path: str,
    page_indices: list[int], reader: pypdf.PdfReader,
) -> None:
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    total_pages = len(reader.pages)
    all_pages = page_indices == list(range(total_pages))
    if all_pages and shutil.which("pdfimages"):
        subprocess.run(
            ["pdfimages", "-png", input_path, str(out_dir / "img")],
            check=True,
        )
        print(f"Extracted images → {out_dir}")
        return

    count = 0
    for i in tqdm(page_indices, desc="Extracting images", unit="page"):
        for j, img in enumerate(reader.pages[i].images):
            ext = img.name.split(".")[-1].lower() if "." in img.name else "png"
            dest = out_dir / f"page_{i + 1:03d}_img_{j + 1:03d}.{ext}"
            dest.write_bytes(img.data)
            count += 1
    print(f"Extracted {count} image(s) → {out_dir}")


def _extract_tables(
    input_path: str, output_path: str, page_indices: list[int]
) -> None:
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    with pdfplumber.open(input_path) as pdf:
        for i in tqdm(page_indices, desc="Extracting tables", unit="page"):
            for j, table in enumerate(pdf.pages[i].extract_tables()):
                dest = out_dir / f"page_{i + 1:03d}_table_{j + 1:03d}.csv"
                with open(dest, "w", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerows(table)
                count += 1
    print(f"Extracted {count} table(s) → {out_dir}")


def _extract_pages(
    input_path: str, output_path: str, page_indices: list[int]
) -> None:
    from pdf2image import convert_from_path

    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    images = convert_from_path(input_path)
    for i in tqdm(page_indices, desc="Rendering pages", unit="page"):
        images[i].save(str(out_dir / f"page_{i + 1:03d}.png"), "PNG")
    print(f"Exported {len(page_indices)} page(s) as PNG → {out_dir}")
