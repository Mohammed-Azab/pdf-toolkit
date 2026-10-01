from __future__ import annotations

import io
from pathlib import Path

import pypdf
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas as rl_canvas
from tqdm import tqdm

from utils import atomic_write, parse_pages
from utils.crop import parse_box
from utils.pdf_info import detect_pdf_type

_CORNERS = {"top-left", "top-right", "bottom-left", "bottom-right"}


def _corner_box(
    corner: str, width_pct: float, height_pct: float, w: float, h: float
) -> tuple[float, float, float, float]:
    bw, bh = w * width_pct / 100, h * height_pct / 100
    if corner == "bottom-right":
        return (w - bw, 0, w, bh)
    if corner == "bottom-left":
        return (0, 0, bw, bh)
    if corner == "top-right":
        return (w - bw, h - bh, w, h)
    if corner == "top-left":
        return (0, h - bh, bw, h)
    raise ValueError(f"Invalid corner '{corner}'. Use: {', '.join(sorted(_CORNERS))}.")


def redact(
    input_path: str | Path,
    output_path: str | Path,
    box: str | None = None,
    corner: str | None = None,
    width_pct: float | None = None,
    height_pct: float | None = None,
    color: str = "#FFFFFF",
    pages: str = "all",
    dry_run: bool = False,
) -> None:
    input_path, output_path = str(input_path), str(output_path)

    if not box and not corner:
        raise ValueError(
            "Provide --box 'x1,y1,x2,y2' or --corner with --width-pct/--height-pct."
        )
    if box and corner:
        raise ValueError("Provide either --box or --corner, not both.")
    if corner:
        if corner not in _CORNERS:
            raise ValueError(f"Invalid corner '{corner}'. Use: {', '.join(sorted(_CORNERS))}.")
        if not width_pct or not height_pct:
            raise ValueError("--corner requires --width-pct and --height-pct.")

    info = detect_pdf_type(input_path)
    if info.type == "encrypted":
        raise RuntimeError(f"{input_path} is encrypted. Unlock it first.")

    reader = pypdf.PdfReader(input_path)
    page_indices = set(parse_pages(pages, len(reader.pages)))
    fixed_box = parse_box(box) if box else None

    if dry_run:
        where = fixed_box if fixed_box else f"{corner} {width_pct}%x{height_pct}%"
        print(
            f"[dry-run] Would redact {len(page_indices)} page(s) "
            f"at {where} → {output_path}"
        )
        return

    writer = pypdf.PdfWriter()
    for i, page in enumerate(tqdm(reader.pages, desc="Redacting", unit="page")):
        if i in page_indices:
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            page_box = fixed_box or _corner_box(corner, width_pct, height_pct, w, h)
            overlay = _make_overlay(w, h, page_box, color)
            page.merge_page(pypdf.PdfReader(overlay).pages[0])
        writer.add_page(page)

    def _write(tmp: str) -> None:
        with open(tmp, "wb") as f:
            writer.write(f)

    atomic_write(output_path, _write)
    print(f"Redacted {len(page_indices)} page(s) → {output_path}")


def _make_overlay(
    w: float, h: float, box: tuple[float, float, float, float], color: str
) -> io.BytesIO:
    x1, y1, x2, y2 = box
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(w, h))
    c.setFillColor(HexColor(color))
    c.rect(x1, y1, x2 - x1, y2 - y1, fill=1, stroke=0)
    c.save()
    buf.seek(0)
    return buf
