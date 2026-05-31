from __future__ import annotations

from pathlib import Path

import pypdf
from tqdm import tqdm

from utils import atomic_write, parse_pages
from utils.pdf_info import detect_pdf_type

_VALID_ANGLES = {90, 180, 270, -90}


def rotate(
    input_path: str | Path,
    output_path: str | Path,
    angle: int,
    pages: str = "all",
    dry_run: bool = False,
) -> None:
    input_path, output_path = str(input_path), str(output_path)

    if angle not in _VALID_ANGLES:
        raise ValueError(
            f"Invalid angle {angle}. Must be one of {sorted(_VALID_ANGLES)}."
        )
    if angle == -90:
        angle = 270

    info = detect_pdf_type(input_path)
    if info.type == "encrypted":
        raise RuntimeError(f"{input_path} is encrypted. Unlock it first.")
    if info.type == "form":
        print(
            "Warning: PDF contains form fields. "
            "Rotation may displace interactive field positions."
        )
    elif info.type in ("scanned", "mixed"):
        print(
            "Warning: PDF contains scanned/image pages. "
            "Rotation is visual-only — OCR orientation is not corrected."
        )

    reader = pypdf.PdfReader(input_path)
    page_indices = set(parse_pages(pages, len(reader.pages)))

    if dry_run:
        print(
            f"[dry-run] Would rotate pages {[i + 1 for i in page_indices]} "
            f"by {angle}° → {output_path}"
        )
        return

    writer = pypdf.PdfWriter()
    for i, page in enumerate(tqdm(reader.pages, desc="Rotating", unit="page")):
        writer.add_page(page)
        if i in page_indices:
            writer.pages[i].rotate(angle)

    def _write(tmp: str) -> None:
        with open(tmp, "wb") as f:
            writer.write(f)

    atomic_write(output_path, _write)
    print(f"Rotated {len(page_indices)} page(s) by {angle}° → {output_path}")
