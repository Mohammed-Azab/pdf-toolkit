from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pypdf

from utils import atomic_write
from utils.pdf_info import detect_pdf_type

_QUALITY_MAP = {
    "screen": "/screen",
    "ebook": "/ebook",
    "printer": "/printer",
    "prepress": "/prepress",
}


def compress(
    input_path: str | Path,
    output_path: str | Path,
    quality: str = "printer",
    dry_run: bool = False,
) -> None:
    input_path, output_path = str(input_path), str(output_path)

    if quality not in _QUALITY_MAP:
        raise ValueError(
            f"Invalid quality '{quality}'. "
            f"Choose from: {list(_QUALITY_MAP.keys())}"
        )

    info = detect_pdf_type(input_path)
    if info.type == "encrypted":
        raise RuntimeError(f"{input_path} is encrypted. Unlock it first.")

    before = os.path.getsize(input_path)

    if dry_run:
        print(
            f"[dry-run] Would compress {input_path} "
            f"(type={info.type}, quality={quality}) → {output_path}"
        )
        return

    if info.type == "text":
        _compress_lossless(input_path, output_path)
    else:
        _compress_ghostscript(input_path, output_path, quality)

    after = os.path.getsize(output_path)
    ratio = (1 - after / before) * 100 if before else 0
    print(
        f"Compressed: {before:,} → {after:,} bytes "
        f"({ratio:.1f}% reduction) → {output_path}"
    )


def _compress_lossless(input_path: str, output_path: str) -> None:
    reader = pypdf.PdfReader(input_path)
    writer = pypdf.PdfWriter()
    writer.append(reader)
    writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)

    def _write_pypdf(tmp: str) -> None:
        with open(tmp, "wb") as f:
            writer.write(f)

    if not shutil.which("qpdf"):
        print("Warning: qpdf not found. Using pypdf-only compression.")
        atomic_write(output_path, _write_pypdf)
        return

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        mid = tf.name
    try:
        _write_pypdf(mid)
        cmd = [
            "qpdf", "--linearize",
            "--compress-streams=y",
            "--object-streams=generate",
            mid, output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"qpdf failed: {result.stderr.strip()}")
    finally:
        if os.path.exists(mid):
            os.remove(mid)


def _compress_ghostscript(input_path: str, output_path: str, quality: str) -> None:
    gs = (
        shutil.which("gs")
        or shutil.which("gswin64c")
        or shutil.which("gswin32c")
    )
    if not gs:
        print(
            "Warning: Ghostscript not found — falling back to pypdf compression.\n"
            "Install:  apt: ghostscript | brew: ghostscript | choco: ghostscript"
        )
        _compress_lossless(input_path, output_path)
        return

    tmp = output_path + ".tmp"
    cmd = [
        gs, "-sDEVICE=pdfwrite", "-dNOPAUSE", "-dBATCH", "-dSAFER",
        f"-dPDFSETTINGS={_QUALITY_MAP[quality]}",
        f"-sOutputFile={tmp}",
        input_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Ghostscript failed: {result.stderr.strip()}")
    os.replace(tmp, output_path)
