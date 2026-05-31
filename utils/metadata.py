from __future__ import annotations

from pathlib import Path

import pypdf

from utils import atomic_write
from utils.pdf_info import detect_pdf_type


def read_metadata(path: str | Path) -> dict[str, str]:
    reader = pypdf.PdfReader(str(path))
    return dict(reader.metadata or {})


def write_metadata(
    input_path: str | Path,
    output_path: str | Path,
    dry_run: bool = False,
    **fields: str,
) -> None:
    input_path, output_path = str(input_path), str(output_path)

    if detect_pdf_type(input_path).type == "encrypted":
        raise RuntimeError(f"{input_path} is encrypted. Unlock it first.")

    if dry_run:
        print(f"[dry-run] Would update metadata fields: {list(fields.keys())}")
        return

    reader = pypdf.PdfReader(input_path)
    writer = pypdf.PdfWriter()
    writer.append(reader)

    existing = dict(reader.metadata or {})
    for key, value in fields.items():
        normalized = f"/{key[0].upper() + key[1:]}" if not key.startswith("/") else key
        existing[normalized] = value
    writer.add_metadata(existing)

    def _write(tmp: str) -> None:
        with open(tmp, "wb") as f:
            writer.write(f)

    atomic_write(output_path, _write)
    print(f"Updated {len(fields)} metadata field(s) → {output_path}")
