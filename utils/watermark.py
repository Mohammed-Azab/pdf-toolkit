from __future__ import annotations

import io
from pathlib import Path

import pypdf
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas as rl_canvas
from tqdm import tqdm

from utils import atomic_write, parse_pages
from utils.pdf_info import detect_pdf_type


def watermark(
    input_path: str | Path,
    output_path: str | Path,
    text: str | None = None,
    image: str | None = None,
    font_size: int = 48,
    opacity: float = 0.3,
    color: str = "#FF0000",
    position: str = "center",
    scale: float = 0.2,
    pages: str = "all",
    dry_run: bool = False,
) -> None:
    input_path, output_path = str(input_path), str(output_path)

    if text is None and image is None:
        raise ValueError("Provide either --text or --image (neither given).")
    if text is not None and image is not None:
        raise ValueError("Provide either --text or --image, not both.")
    if not (0.0 <= opacity <= 1.0):
        raise ValueError(
            f"opacity must be 0.0–1.0, got {opacity}."
        )

    info = detect_pdf_type(input_path)
    if info.type == "encrypted":
        raise RuntimeError(f"{input_path} is encrypted. Unlock it first.")
    if info.type in ("scanned", "mixed"):
        print("Warning: watermark is added as a vector overlay on scanned pages.")

    reader = pypdf.PdfReader(input_path)
    page_indices = set(parse_pages(pages, len(reader.pages)))

    _VALID_POSITIONS = {"center", "top-right", "bottom-left"}
    if image is not None and position not in _VALID_POSITIONS:
        raise ValueError(
            f"Invalid position '{position}'. Use: center, top-right, bottom-left."
        )

    if dry_run:
        label = f"text='{text}'" if text else f"image='{image}'"
        print(
            f"[dry-run] Would apply watermark ({label}) "
            f"to {len(page_indices)} page(s) → {output_path}"
        )
        return

    writer = pypdf.PdfWriter()
    for i, page in enumerate(
        tqdm(reader.pages, desc="Watermarking", unit="page")
    ):
        if i in page_indices:
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            buf = (
                _text_watermark(text, w, h, font_size, opacity, color)
                if text
                else _image_watermark(image, w, h, position, scale, opacity)
            )
            wm_page = pypdf.PdfReader(buf).pages[0]
            page.merge_page(wm_page)
        writer.add_page(page)

    def _write(tmp: str) -> None:
        with open(tmp, "wb") as f:
            writer.write(f)

    atomic_write(output_path, _write)
    print(f"Watermarked {len(page_indices)} page(s) → {output_path}")


def _text_watermark(
    text: str, w: float, h: float,
    font_size: int, opacity: float, color: str,
) -> io.BytesIO:
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(w, h))
    c.setFillColor(HexColor(color))
    c.setFillAlpha(opacity)
    c.setFont("Helvetica-Bold", font_size)
    c.translate(w / 2, h / 2)
    c.rotate(45)
    c.drawCentredString(0, 0, text)
    c.save()
    buf.seek(0)
    return buf


def _image_watermark(
    image_path: str, w: float, h: float,
    position: str, scale: float, opacity: float,
) -> io.BytesIO:
    from PIL import Image as PILImage

    img = PILImage.open(image_path)
    iw, ih = img.size
    draw_w = w * scale
    draw_h = draw_w * (ih / iw)

    coords = {
        "center": (w / 2 - draw_w / 2, h / 2 - draw_h / 2),
        "top-right": (w - draw_w - 20, h - draw_h - 20),
        "bottom-left": (20.0, 20.0),
    }
    x, y = coords[position]

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(w, h))
    c.drawImage(image_path, x, y, width=draw_w, height=draw_h, mask="auto")
    c.save()
    buf.seek(0)
    return buf
