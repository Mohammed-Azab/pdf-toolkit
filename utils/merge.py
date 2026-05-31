from __future__ import annotations

from pathlib import Path

import pypdf
from tqdm import tqdm

from utils import atomic_write
from utils.pdf_info import detect_pdf_type


def merge(
    input_paths: list[str | Path],
    output_path: str | Path,
    interleave: bool = False,
    dry_run: bool = False,
) -> None:
    output_path = str(output_path)
    input_paths = [str(p) for p in input_paths]

    for p in input_paths:
        if detect_pdf_type(p).type == "encrypted":
            raise RuntimeError(f"{p} is encrypted. Unlock it first.")

    if interleave and len(input_paths) != 2:
        raise ValueError("--interleave requires exactly 2 input files.")

    readers = [pypdf.PdfReader(p) for p in input_paths]

    if dry_run:
        total = sum(len(r.pages) for r in readers)
        print(
            f"[dry-run] Would merge {len(input_paths)} file(s) "
            f"({total} total pages) → {output_path}"
        )
        return

    writer = pypdf.PdfWriter()

    if interleave:
        a, b = readers
        for i in range(max(len(a.pages), len(b.pages))):
            if i < len(a.pages):
                writer.add_page(a.pages[i])
            if i < len(b.pages):
                writer.add_page(b.pages[i])
    else:
        for reader in tqdm(readers, desc="Merging", unit="file"):
            writer.append(reader)

    def _write(tmp: str) -> None:
        with open(tmp, "wb") as f:
            writer.write(f)

    atomic_write(output_path, _write)
    print(f"Merged {len(input_paths)} file(s) → {output_path}")
