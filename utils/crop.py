from __future__ import annotations

from pathlib import Path

import pypdf
from pypdf.generic import RectangleObject
from tqdm import tqdm

from utils import atomic_write, parse_pages
from utils.pdf_info import detect_pdf_type


def parse_box(box_str: str) -> tuple[float, float, float, float]:
    parts = [p.strip() for p in box_str.split(",")]
    if len(parts) != 4:
        raise ValueError(
            f"Invalid box '{box_str}'. Expected: x1,y1,x2,y2 in PDF points."
        )
    return (float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]))


def crop(
    input_path: str | Path,
    output_path: str | Path,
    box: str | None = None,
    pages: str = "all",
    gui: bool = False,
    dry_run: bool = False,
) -> None:
    input_path, output_path = str(input_path), str(output_path)

    if not gui and not box:
        raise ValueError("Provide --box 'x1,y1,x2,y2' or use --gui.")
    if gui and box:
        raise ValueError("Provide either --box or --gui, not both.")

    info = detect_pdf_type(input_path)
    if info.type == "encrypted":
        raise RuntimeError(f"{input_path} is encrypted. Unlock it first.")

    reader = pypdf.PdfReader(input_path)
    page_indices = parse_pages(pages, len(reader.pages))

    if gui:
        box_coords = _launch_gui(input_path, reader)
        if box_coords is None:
            print("Crop cancelled.")
            return
    else:
        box_coords = parse_box(box)  # type: ignore[arg-type]

    if dry_run:
        print(
            f"[dry-run] Would crop {len(page_indices)} page(s) "
            f"to box {box_coords} → {output_path}"
        )
        return

    x1, y1, x2, y2 = box_coords
    page_index_set = set(page_indices)
    writer = pypdf.PdfWriter()
    for i, page in enumerate(tqdm(reader.pages, desc="Cropping", unit="page")):
        writer.add_page(page)
        if i in page_index_set:
            writer.pages[i].cropbox = RectangleObject([x1, y1, x2, y2])

    def _write(tmp: str) -> None:
        with open(tmp, "wb") as f:
            writer.write(f)

    atomic_write(output_path, _write)
    print(f"Cropped {len(page_indices)} page(s) to box {box_coords} → {output_path}")


def _launch_gui(
    input_path: str, reader: pypdf.PdfReader
) -> tuple[float, float, float, float] | None:
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        raise RuntimeError(
            "tkinter is not available.\n"
            "Install:  apt: python3-tk | brew: python-tk@3.x | "
            "Windows: reinstall Python with tcl/tk option"
        )

    from pdf2image import convert_from_path
    from PIL import ImageTk

    images = convert_from_path(input_path, first_page=1, last_page=1)
    pil_img = images[0]

    page = reader.pages[0]
    pdf_w = float(page.mediabox.width)
    pdf_h = float(page.mediabox.height)
    canvas_w = 800
    canvas_h = int(canvas_w * pdf_h / pdf_w)
    scale_x = pdf_w / canvas_w
    scale_y = pdf_h / canvas_h

    pil_img = pil_img.resize((canvas_w, canvas_h))

    result: list[tuple[float, float, float, float] | None] = [None]

    root = tk.Tk()
    root.title("PDF Crop — Draw rectangle to select crop area")

    tk_img = ImageTk.PhotoImage(pil_img)
    cv = tk.Canvas(root, width=canvas_w, height=canvas_h)
    cv.pack()
    cv.create_image(0, 0, anchor="nw", image=tk_img)

    coord_var = tk.StringVar(value="Click and drag to select crop area")
    tk.Label(root, textvariable=coord_var).pack()

    state: dict = {"start": None, "rect": None, "end": None}

    def on_press(e):
        state["start"] = (e.x, e.y)
        if state["rect"]:
            cv.delete(state["rect"])

    def on_drag(e):
        if not state["start"]:
            return
        x0, y0 = state["start"]
        if state["rect"]:
            cv.delete(state["rect"])
        state["rect"] = cv.create_rectangle(x0, y0, e.x, e.y, outline="red", width=2)
        pts = _px_to_pts(x0, y0, e.x, e.y, canvas_h, scale_x, scale_y)
        coord_var.set(f"Box: {pts[0]:.1f}, {pts[1]:.1f}, {pts[2]:.1f}, {pts[3]:.1f} pts")

    def on_release(e):
        state["end"] = (e.x, e.y)

    cv.bind("<ButtonPress-1>", on_press)
    cv.bind("<B1-Motion>", on_drag)
    cv.bind("<ButtonRelease-1>", on_release)

    frame = tk.Frame(root)
    frame.pack(fill="x")

    def apply_this():
        if state["start"] and state["end"]:
            x0, y0 = state["start"]
            x1, y1 = state["end"]
            result[0] = _px_to_pts(x0, y0, x1, y1, canvas_h, scale_x, scale_y)
        root.destroy()

    def cancel():
        root.destroy()

    ttk.Button(frame, text="Apply to this page", command=apply_this).pack(side="left")
    ttk.Button(frame, text="Apply to all pages", command=apply_this).pack(side="left")
    ttk.Button(frame, text="Cancel", command=cancel).pack(side="right")

    root.mainloop()
    return result[0]


def _px_to_pts(
    x0: int, y0: int, x1: int, y1: int,
    canvas_h: int, scale_x: float, scale_y: float,
) -> tuple[float, float, float, float]:
    left = min(x0, x1) * scale_x
    right = max(x0, x1) * scale_x
    bottom = (canvas_h - max(y0, y1)) * scale_y
    top = (canvas_h - min(y0, y1)) * scale_y
    return (left, bottom, right, top)
