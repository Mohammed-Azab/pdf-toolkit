from __future__ import annotations

import os
from pathlib import Path

from tqdm import tqdm

from utils import atomic_write, parse_pages
from utils.normalize import _NAMED_SIZES, parse_size
from utils.pdf_info import detect_pdf_type

_IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".gif"}
_VALID_FORMATS = {"png", "jpg", "webp", "tiff"}


def img_to_pdf(
    image_paths: list[str | Path],
    output_path: str | Path,
    size: str = "fit",
    dry_run: bool = False,
) -> None:
    output_path = str(output_path)
    paths = [str(p) for p in image_paths]

    if not paths:
        raise ValueError("No image files provided.")

    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        raise FileNotFoundError(f"Image(s) not found: {missing}")

    bad_ext = [p for p in paths if Path(p).suffix.lower() not in _IMG_EXTENSIONS]
    if bad_ext:
        raise ValueError(
            f"Unsupported file type(s): {bad_ext}. "
            f"Supported: {sorted(_IMG_EXTENSIONS)}"
        )

    if dry_run:
        print(
            f"[dry-run] Would convert {len(paths)} image(s) to PDF "
            f"(size={size}) → {output_path}"
        )
        return

    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas as rl_canvas

    import io

    buf = io.BytesIO()
    # Determine page size for first page — reportlab needs it at Canvas creation
    first_w, first_h = _page_dims(paths[0], size)
    c = rl_canvas.Canvas(buf, pagesize=(first_w, first_h))

    for i, img_path in enumerate(tqdm(paths, desc="Converting images", unit="img")):
        pw, ph = _page_dims(img_path, size)
        if i > 0:
            c.setPageSize((pw, ph))

        from PIL import Image as PILImage
        with PILImage.open(img_path) as img:
            iw, ih = img.size

        scale = min(pw / iw, ph / ih)
        draw_w, draw_h = iw * scale, ih * scale
        x = (pw - draw_w) / 2
        y = (ph - draw_h) / 2

        c.drawImage(ImageReader(img_path), x, y, width=draw_w, height=draw_h)
        c.showPage()

    c.save()

    def _write(tmp: str) -> None:
        with open(tmp, "wb") as f:
            f.write(buf.getvalue())

    atomic_write(output_path, _write)
    print(f"Converted {len(paths)} image(s) → {output_path}")


def pdf_to_img(
    input_path: str | Path,
    output_dir: str | Path,
    fmt: str = "png",
    dpi: int = 150,
    pages: str = "all",
    dry_run: bool = False,
) -> None:
    import pypdf

    input_path = str(input_path)
    output_dir = Path(output_dir)
    fmt = fmt.lower()
    stem = Path(input_path).stem

    if fmt not in _VALID_FORMATS:
        raise ValueError(f"Invalid format '{fmt}'. Choose from: {sorted(_VALID_FORMATS)}")
    if dpi < 1:
        raise ValueError(f"DPI must be a positive integer, got {dpi}.")

    info = detect_pdf_type(input_path)
    if info.type == "encrypted":
        raise RuntimeError(f"{input_path} is encrypted. Unlock it first.")

    reader = pypdf.PdfReader(input_path)
    page_indices = parse_pages(pages, len(reader.pages))

    if dry_run:
        print(
            f"[dry-run] Would export {len(page_indices)} page(s) "
            f"as {fmt.upper()} at {dpi} DPI → {output_dir}/"
        )
        return

    from pdf2image import convert_from_path

    output_dir.mkdir(parents=True, exist_ok=True)
    first = min(page_indices) + 1
    last = max(page_indices) + 1

    images = convert_from_path(input_path, dpi=dpi, first_page=first, last_page=last)

    # pdf2image returns pages first..last; re-index against page_indices
    offset = first - 1
    save_fmt = "JPEG" if fmt == "jpg" else fmt.upper()
    ext = "jpg" if fmt == "jpg" else fmt

    for img, page_idx in tqdm(
        zip(images, range(first - 1, last)),
        total=len(images),
        desc="Exporting pages",
        unit="page",
    ):
        if page_idx in page_indices:
            dest = output_dir / f"{stem}_page_{page_idx + 1:03d}.{ext}"
            img.save(str(dest), save_fmt)

    print(f"Exported {len(page_indices)} page(s) as {fmt.upper()} ({dpi} DPI) → {output_dir}/")


def _page_dims(img_path: str, size: str) -> tuple[float, float]:
    """Return page dimensions in PDF points for this image given size spec."""
    if size == "fit":
        from PIL import Image as PILImage
        with PILImage.open(img_path) as img:
            # 72 points per inch; assume 96 DPI screen resolution for "fit"
            w_pt = img.width * 72 / 96
            h_pt = img.height * 72 / 96
        return (w_pt, h_pt)
    return parse_size(size)
