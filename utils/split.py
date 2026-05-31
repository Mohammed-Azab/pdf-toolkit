from __future__ import annotations

import math
from pathlib import Path

import pypdf
from tqdm import tqdm

from utils import atomic_write
from utils.pdf_info import detect_pdf_type


def split(
    input_path: str | Path,
    output_dir: str | Path,
    mode: str = "pages",
    ranges: str | None = None,
    chunk_size: int | None = None,
    dry_run: bool = False,
) -> None:
    input_path = str(input_path)
    output_dir = Path(output_dir)
    stem = Path(input_path).stem

    info = detect_pdf_type(input_path)
    if info.type == "encrypted":
        raise RuntimeError(f"{input_path} is encrypted. Unlock it first.")

    reader = pypdf.PdfReader(input_path)
    total = len(reader.pages)

    if mode == "pages":
        groups = [[i] for i in range(total)]
        names = [f"{stem}_page_{i + 1:03d}.pdf" for i in range(total)]
    elif mode == "range":
        if not ranges:
            raise ValueError("--ranges is required for range mode.")
        groups, names = _parse_ranges(ranges, total, stem)
    elif mode == "size":
        if chunk_size is None or chunk_size < 1:
            raise ValueError("--chunk-size must be a positive integer.")
        n = math.ceil(total / chunk_size)
        groups = [
            list(range(i * chunk_size, min((i + 1) * chunk_size, total)))
            for i in range(n)
        ]
        names = [f"{stem}_chunk_{i + 1:03d}.pdf" for i in range(n)]
    else:
        raise ValueError(f"Unknown mode '{mode}'. Use: pages, range, size.")

    if dry_run:
        for name, group in zip(names, groups):
            print(f"[dry-run] Would write {output_dir / name} ({len(group)} page(s))")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    for name, group in tqdm(zip(names, groups), total=len(names), desc="Splitting", unit="file"):
        writer = pypdf.PdfWriter()
        for idx in group:
            writer.add_page(reader.pages[idx])
        atomic_write(str(output_dir / name), _make_writer_fn(writer))

    print(f"Split into {len(groups)} file(s) in {output_dir}")


def _make_writer_fn(writer: pypdf.PdfWriter):
    def _write(tmp: str) -> None:
        with open(tmp, "wb") as f:
            writer.write(f)
    return _write


def _parse_ranges(spec: str, total: int, stem: str) -> tuple[list[list[int]], list[str]]:
    groups: list[list[int]] = []
    names: list[str] = []
    for i, part in enumerate(spec.split(",")):
        part = part.strip()
        if not part:
            raise ValueError(f"Invalid ranges spec '{spec}': empty token.")
        if "-" in part:
            halves = part.split("-", 1)
            try:
                a, b = int(halves[0].strip()), int(halves[1].strip())
            except ValueError:
                raise ValueError(f"Invalid page range '{part}' in ranges spec '{spec}'.")
            if b < a:
                raise ValueError(
                    f"Invalid range '{part}': end page must be >= start page."
                )
            group = list(range(a - 1, b))
        else:
            try:
                n = int(part)
            except ValueError:
                raise ValueError(f"Invalid page number '{part}' in ranges spec '{spec}'.")
            group = [n - 1]
        for idx in group:
            if idx < 0 or idx >= total:
                raise ValueError(
                    f"Page {idx + 1} does not exist — this PDF has {total} pages."
                )
        groups.append(group)
        names.append(f"{stem}_part_{i + 1:03d}.pdf")
    return groups, names
