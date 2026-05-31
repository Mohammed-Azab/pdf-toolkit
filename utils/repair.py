from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pypdf

from utils import atomic_write


def repair(
    input_path: str | Path,
    output_path: str | Path,
    dry_run: bool = False,
) -> None:
    input_path, output_path = str(input_path), str(output_path)

    if dry_run:
        print(f"[dry-run] Would attempt repair: {input_path} → {output_path}")
        return

    # Strategy 1: pypdf with strict=False — handles truncated xref tables,
    # missing EOF markers, and minor structural issues.
    if _try_pypdf(input_path, output_path):
        print(f"Repaired via pypdf → {output_path}")
        return

    # Strategy 2: qpdf --recover — handles more structural damage including
    # broken object streams and damaged cross-reference sections.
    if shutil.which("qpdf") and _try_qpdf(input_path, output_path):
        print(f"Repaired via qpdf → {output_path}")
        return

    # Strategy 3: Ghostscript — re-renders the entire PDF, recovering content
    # from files with severe structural damage at the cost of losing metadata,
    # bookmarks, and form fields.
    gs = shutil.which("gs") or shutil.which("gswin64c") or shutil.which("gswin32c")
    if gs and _try_ghostscript(gs, input_path, output_path):
        print(f"Repaired via Ghostscript (content re-rendered) → {output_path}")
        return

    raise RuntimeError(
        f"Could not repair '{input_path}'. All strategies failed.\n"
        "The file may be too severely damaged to recover.\n"
        "Tips:\n"
        "  • Install qpdf:  apt: sudo apt-get install qpdf\n"
        "  • Install gs:    apt: sudo apt-get install ghostscript"
    )


def _try_pypdf(input_path: str, output_path: str) -> bool:
    try:
        reader = pypdf.PdfReader(input_path, strict=False)
        writer = pypdf.PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        def _write(tmp: str) -> None:
            with open(tmp, "wb") as f:
                writer.write(f)

        atomic_write(output_path, _write)
        # Verify the output is readable
        pypdf.PdfReader(output_path, strict=False)
        return True
    except Exception as exc:
        print(f"  pypdf strategy failed: {exc}")
        return False


def _try_qpdf(input_path: str, output_path: str) -> bool:
    try:
        result = subprocess.run(
            ["qpdf", "--recover", "--replace-input", input_path, output_path],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            return True
        # qpdf exit code 3 means "warnings but succeeded"
        if result.returncode == 3:
            if result.stderr:
                print(f"  qpdf warnings: {result.stderr.strip()}")
            return True
        print(f"  qpdf strategy failed: {result.stderr.strip()}")
        return False
    except Exception as exc:
        print(f"  qpdf strategy failed: {exc}")
        return False


def _try_ghostscript(gs: str, input_path: str, output_path: str) -> bool:
    try:
        result = subprocess.run(
            [
                gs, "-sDEVICE=pdfwrite", "-dNOPAUSE", "-dBATCH", "-dSAFER",
                "-dPDFSETTINGS=/prepress",
                f"-sOutputFile={output_path}",
                input_path,
            ],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            return True
        print(f"  Ghostscript strategy failed: {result.stderr.strip()[:200]}")
        return False
    except Exception as exc:
        print(f"  Ghostscript strategy failed: {exc}")
        return False
