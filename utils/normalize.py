from __future__ import annotations

from pathlib import Path

import pypdf
from pypdf import Transformation
from pypdf.generic import RectangleObject
from tqdm import tqdm

from utils import atomic_write
from utils.pdf_info import detect_pdf_type

_NAMED_SIZES: dict[str, tuple[float, float]] = {
    "a4":           (595.28, 841.89),
    "a4-landscape": (841.89, 595.28),
    "a3":           (841.89, 1190.55),
    "a3-landscape": (1190.55, 841.89),
    "letter":       (612.0,  792.0),
    "legal":        (612.0,  1008.0),
}


def parse_size(size_str: str) -> tuple[float, float]:
    """Accept 'a4', 'letter', or 'WxH' (points). Returns (width, height)."""
    key = size_str.strip().lower()
    if key in _NAMED_SIZES:
        return _NAMED_SIZES[key]
    if "x" in key:
        parts = key.split("x", 1)
        try:
            w, h = float(parts[0]), float(parts[1])
        except ValueError:
            raise ValueError(f"Invalid size '{size_str}'. Use 'a4', 'letter', or 'WxH' in points.")
        if w <= 0 or h <= 0:
            raise ValueError(f"Size dimensions must be positive, got {size_str!r}.")
        return (w, h)
    raise ValueError(
        f"Unknown size '{size_str}'. "
        f"Use one of {list(_NAMED_SIZES)} or 'WxH' in PDF points (1pt = 1/72 inch)."
    )


def normalize(
    input_path: str | Path,
    output_path: str | Path,
    size: str = "a4",
    dry_run: bool = False,
) -> None:
    input_path, output_path = str(input_path), str(output_path)

    target_w, target_h = parse_size(size)

    info = detect_pdf_type(input_path)
    if info.type == "encrypted":
        raise RuntimeError(f"{input_path} is encrypted. Unlock it first.")

    reader = pypdf.PdfReader(input_path)
    total = len(reader.pages)

    if dry_run:
        print(
            f"[dry-run] Would normalize {total} page(s) to "
            f"{target_w:.1f}x{target_h:.1f}pt ({size}) → {output_path}"
        )
        return

    writer = pypdf.PdfWriter()
    for page in tqdm(reader.pages, desc="Normalizing", unit="page"):
        orig_w = float(page.mediabox.width)
        orig_h = float(page.mediabox.height)

        scale = min(target_w / orig_w, target_h / orig_h)
        tx = (target_w - orig_w * scale) / 2
        ty = (target_h - orig_h * scale) / 2

        page.add_transformation(Transformation().scale(scale, scale).translate(tx, ty))
        page.mediabox = RectangleObject([0, 0, target_w, target_h])

        writer.add_page(page)

    def _write(tmp: str) -> None:
        with open(tmp, "wb") as f:
            writer.write(f)

    atomic_write(output_path, _write)
    print(
        f"Normalized {total} page(s) to {target_w:.1f}x{target_h:.1f}pt ({size}) → {output_path}"
    )
