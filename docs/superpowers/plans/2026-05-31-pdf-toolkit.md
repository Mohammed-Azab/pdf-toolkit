# PDF Toolkit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-ready Python CLI toolkit for PDF editing with 10 operation modules, a shared utility layer, comprehensive tests, and a full README.

**Architecture:** Flat module design — `main.py` dispatches argparse subcommands to independent `utils/` modules. `pdf_info.py` is called first in every operation to detect PDF type and gate behavior. `utils/__init__.py` provides `parse_pages()` and `atomic_write()` shared by all modules. External tools (Ghostscript, qpdf, tesseract) are detected at runtime via `shutil.which()` with graceful fallback or clear error messages.

**Tech Stack:** pypdf>=4.0.0, pdfplumber>=0.10.0, reportlab>=4.0.0, pdf2image>=1.17.0, Pillow>=10.0.0, pytesseract>=0.3.10, tqdm>=4.0.0, tkinter (stdlib), pytest>=7.0.0

---

## File Map

| File | Responsibility |
|---|---|
| `requirements.txt` | Python package pins |
| `utils/__init__.py` | `parse_pages()`, `atomic_write()` |
| `utils/pdf_info.py` | `detect_pdf_type()` → `PDFInfo` dataclass |
| `utils/rotate.py` | `rotate(input, output, angle, pages, dry_run)` |
| `utils/split.py` | `split(input, output_dir, mode, ranges, chunk_size, dry_run)` |
| `utils/merge.py` | `merge(inputs, output, interleave, dry_run)` |
| `utils/metadata.py` | `read_metadata(input)`, `write_metadata(input, output, **fields, dry_run)` |
| `utils/unlock.py` | `unlock(input, output, password, dry_run)` |
| `utils/compress.py` | `compress(input, output, quality, dry_run)` |
| `utils/watermark.py` | `watermark(input, output, text, image, ..., dry_run)` |
| `utils/extract.py` | `extract(input, output, type_, pages, dry_run)` |
| `utils/crop.py` | `crop(input, output, box, pages, gui, dry_run)`, `parse_box()` |
| `main.py` | argparse subcommand dispatch |
| `tests/conftest.py` | Session-scoped PDF fixtures |
| `tests/test_utils.py` | Unit tests for all modules |
| `README.md` | Installation, usage, compatibility table, troubleshooting |

---

## Task 1: Scaffolding and Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `utils/__init__.py` (stub)
- Create: `utils/pdf_info.py` (stub)
- Create: `utils/compress.py` (stub)
- Create: `utils/crop.py` (stub)
- Create: `utils/rotate.py` (stub)
- Create: `utils/unlock.py` (stub)
- Create: `utils/split.py` (stub)
- Create: `utils/merge.py` (stub)
- Create: `utils/watermark.py` (stub)
- Create: `utils/metadata.py` (stub)
- Create: `utils/extract.py` (stub)
- Create: `tests/__init__.py` (empty)
- Create: `tests/conftest.py` (stub)
- Create: `tests/test_utils.py` (stub)

- [ ] **Step 1: Create directory layout and stubs**

```bash
cd /home/ubuntu/myRepo/repo/pdf-toolkit
mkdir -p utils tests
touch utils/__init__.py utils/pdf_info.py utils/compress.py utils/crop.py \
      utils/rotate.py utils/unlock.py utils/split.py utils/merge.py \
      utils/watermark.py utils/metadata.py utils/extract.py \
      tests/__init__.py tests/conftest.py tests/test_utils.py
```

- [ ] **Step 2: Write `requirements.txt`**

```
pypdf>=4.0.0
pdfplumber>=0.10.0
reportlab>=4.0.0
pdf2image>=1.17.0
Pillow>=10.0.0
pytesseract>=0.3.10
tqdm>=4.0.0
pytest>=7.0.0
```

- [ ] **Step 3: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without errors.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt utils/ tests/
git commit -m "chore: scaffold project structure and dependencies"
```

---

## Task 2: Test Fixtures

**Files:**
- Modify: `tests/conftest.py`

- [ ] **Step 1: Write `tests/conftest.py`**

```python
import pytest
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import pypdf


@pytest.fixture(scope="session")
def text_pdf(tmp_path_factory):
    out = tmp_path_factory.mktemp("pdfs") / "text.pdf"
    c = canvas.Canvas(str(out), pagesize=letter)
    for i in range(3):
        c.drawString(100, 700, f"Page {i + 1}: Hello, PDF toolkit!")
        c.showPage()
    c.save()
    return out


@pytest.fixture(scope="session")
def two_page_pdf(tmp_path_factory):
    out = tmp_path_factory.mktemp("pdfs") / "two.pdf"
    c = canvas.Canvas(str(out), pagesize=letter)
    c.drawString(100, 700, "First PDF - Page 1")
    c.showPage()
    c.drawString(100, 700, "First PDF - Page 2")
    c.showPage()
    c.save()
    return out


@pytest.fixture(scope="session")
def second_pdf(tmp_path_factory):
    out = tmp_path_factory.mktemp("pdfs") / "second.pdf"
    c = canvas.Canvas(str(out), pagesize=letter)
    c.drawString(100, 700, "Second PDF - Page A")
    c.showPage()
    c.drawString(100, 700, "Second PDF - Page B")
    c.showPage()
    c.save()
    return out


@pytest.fixture(scope="session")
def encrypted_pdf(tmp_path_factory, text_pdf):
    out = tmp_path_factory.mktemp("pdfs") / "encrypted.pdf"
    reader = pypdf.PdfReader(str(text_pdf))
    writer = pypdf.PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt("secret")
    with open(out, "wb") as f:
        writer.write(f)
    return out
```

- [ ] **Step 2: Verify fixtures are collected**

```bash
cd /home/ubuntu/myRepo/repo/pdf-toolkit
pytest tests/conftest.py --collect-only
```

Expected: no errors, session starts without import failures.

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add session-scoped PDF fixtures"
```

---

## Task 3: Shared Utilities — `parse_pages` and `atomic_write`

**Files:**
- Modify: `utils/__init__.py`
- Modify: `tests/test_utils.py`

- [ ] **Step 1: Write the failing tests**

Write `tests/test_utils.py` with this full content (all future tasks append to this file):

```python
import os
import shutil
from pathlib import Path

import pdfplumber
import pypdf
import pytest

from utils import atomic_write, parse_pages


# ---------------------------------------------------------------------------
# parse_pages / atomic_write
# ---------------------------------------------------------------------------

def test_parse_pages_all():
    assert parse_pages("all", 5) == [0, 1, 2, 3, 4]


def test_parse_pages_single():
    assert parse_pages("2", 5) == [1]


def test_parse_pages_comma():
    assert parse_pages("1,3", 5) == [0, 2]


def test_parse_pages_range():
    assert parse_pages("2-4", 5) == [1, 2, 3]


def test_parse_pages_mixed():
    assert parse_pages("1,3-5", 5) == [0, 2, 3, 4]


def test_parse_pages_out_of_range():
    with pytest.raises(ValueError, match="Page 7 does not exist"):
        parse_pages("7", 5)


def test_atomic_write(tmp_path):
    out = tmp_path / "out.txt"

    def write_fn(path):
        with open(path, "w") as f:
            f.write("hello")

    atomic_write(str(out), write_fn)
    assert out.read_text() == "hello"
    assert not (tmp_path / "out.txt.tmp").exists()


def test_atomic_write_no_partial_on_error(tmp_path):
    out = tmp_path / "out.txt"
    out.write_text("original")

    def bad_write(path):
        with open(path, "w") as f:
            f.write("partial")
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        atomic_write(str(out), bad_write)

    assert out.read_text() == "original"
```

- [ ] **Step 2: Run to verify failure**

```bash
cd /home/ubuntu/myRepo/repo/pdf-toolkit
pytest tests/test_utils.py::test_parse_pages_all -v
```

Expected: FAIL with `ImportError: cannot import name 'parse_pages' from 'utils'`

- [ ] **Step 3: Implement `utils/__init__.py`**

```python
from __future__ import annotations

import os
from typing import Callable


def parse_pages(spec: str, total: int) -> list[int]:
    """Convert page spec ('all', '1', '1,3', '2-5') to sorted 0-indexed list."""
    if spec.strip().lower() == "all":
        return list(range(total))
    indices: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            for n in range(int(start_s), int(end_s) + 1):
                _check_page(n, total)
                indices.append(n - 1)
        else:
            n = int(part)
            _check_page(n, total)
            indices.append(n - 1)
    return sorted(set(indices))


def _check_page(n: int, total: int) -> None:
    if n < 1 or n > total:
        raise ValueError(
            f"Page {n} does not exist — this PDF has {total} pages."
        )


def atomic_write(path: str, writer_fn: Callable[[str], None]) -> None:
    """Write to path.tmp then os.replace — prevents partial overwrites on crash."""
    tmp = path + ".tmp"
    try:
        writer_fn(tmp)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
```

- [ ] **Step 4: Run all tests so far**

```bash
pytest tests/test_utils.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add utils/__init__.py tests/test_utils.py
git commit -m "feat: add parse_pages and atomic_write shared utilities"
```

---

## Task 4: PDF Type Detection — `pdf_info.py`

**Files:**
- Modify: `utils/pdf_info.py`
- Modify: `tests/test_utils.py` (append the functions below)

- [ ] **Step 1: Append failing tests to `tests/test_utils.py`**

```python
# ---------------------------------------------------------------------------
# pdf_info
# ---------------------------------------------------------------------------

from utils.pdf_info import PDFInfo, detect_pdf_type


def test_pdf_info_text_pdf(text_pdf):
    info = detect_pdf_type(str(text_pdf))
    assert isinstance(info, PDFInfo)
    assert info.type == "text"
    assert info.page_count == 3
    assert info.has_forms is False
    assert info.encryption_type is None


def test_pdf_info_encrypted(encrypted_pdf):
    info = detect_pdf_type(str(encrypted_pdf))
    assert info.type == "encrypted"
    assert info.encryption_type is not None


def test_pdf_info_page_count(two_page_pdf):
    info = detect_pdf_type(str(two_page_pdf))
    assert info.page_count == 2
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_utils.py::test_pdf_info_text_pdf -v
```

Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `utils/pdf_info.py`**

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pdfplumber
import pypdf

_TEXT_THRESHOLD = 10  # minimum chars on a page to count as "text"


@dataclass
class PDFInfo:
    type: Literal["text", "scanned", "mixed", "form", "encrypted"]
    page_count: int
    encryption_type: str | None
    has_forms: bool
    text_page_count: int
    image_only_page_count: int


def detect_pdf_type(path: str | Path) -> PDFInfo:
    path = str(path)
    reader = pypdf.PdfReader(path)

    if reader.is_encrypted:
        return PDFInfo(
            type="encrypted",
            page_count=0,
            encryption_type=_encryption_type(reader),
            has_forms=False,
            text_page_count=0,
            image_only_page_count=0,
        )

    page_count = len(reader.pages)
    has_forms = _has_forms(reader)
    text_pages = 0
    image_only_pages = 0

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if len(text.strip()) >= _TEXT_THRESHOLD:
                text_pages += 1
            elif page.images:
                image_only_pages += 1
            else:
                text_pages += 1  # blank pages count as text

    if has_forms:
        pdf_type: Literal["text", "scanned", "mixed", "form", "encrypted"] = "form"
    elif image_only_pages == 0:
        pdf_type = "text"
    elif text_pages == 0:
        pdf_type = "scanned"
    else:
        pdf_type = "mixed"

    return PDFInfo(
        type=pdf_type,
        page_count=page_count,
        encryption_type=None,
        has_forms=has_forms,
        text_page_count=text_pages,
        image_only_page_count=image_only_pages,
    )


def _has_forms(reader: pypdf.PdfReader) -> bool:
    try:
        return "/AcroForm" in reader.trailer["/Root"]
    except (KeyError, TypeError):
        return False


def _encryption_type(reader: pypdf.PdfReader) -> str:
    try:
        enc = reader.trailer.get("/Encrypt", {})
        v = enc.get("/V", 0)
        if v >= 5:
            return "AES-256"
        if v == 4:
            return "AES-128"
        if v == 2:
            return "RC4-128"
        return f"RC4-40 (V={v})"
    except Exception:
        return "unknown"
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_utils.py -k "pdf_info" -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add utils/pdf_info.py tests/test_utils.py
git commit -m "feat: add PDF type detection (text/scanned/mixed/form/encrypted)"
```

---

## Task 5: Rotate — `rotate.py`

**Files:**
- Modify: `utils/rotate.py`
- Modify: `tests/test_utils.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_utils.py`**

```python
# ---------------------------------------------------------------------------
# rotate
# ---------------------------------------------------------------------------

from utils.rotate import rotate


def test_rotate_all_pages(text_pdf, tmp_path):
    out = str(tmp_path / "rotated.pdf")
    rotate(str(text_pdf), out, angle=90, pages="all")
    reader = pypdf.PdfReader(out)
    assert len(reader.pages) == 3
    assert reader.pages[0].get("/Rotate", 0) == 90


def test_rotate_specific_pages(text_pdf, tmp_path):
    out = str(tmp_path / "rotated2.pdf")
    rotate(str(text_pdf), out, angle=180, pages="2")
    reader = pypdf.PdfReader(out)
    assert reader.pages[1].get("/Rotate", 0) == 180
    assert reader.pages[0].get("/Rotate", 0) == 0


def test_rotate_invalid_angle(text_pdf, tmp_path):
    with pytest.raises(ValueError, match="angle"):
        rotate(str(text_pdf), str(tmp_path / "x.pdf"), angle=45, pages="all")


def test_rotate_dry_run(text_pdf, tmp_path):
    out = str(tmp_path / "dry.pdf")
    rotate(str(text_pdf), out, angle=90, pages="all", dry_run=True)
    assert not os.path.exists(out)
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_utils.py::test_rotate_all_pages -v
```

Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `utils/rotate.py`**

```python
from __future__ import annotations

from pathlib import Path

import pypdf
from tqdm import tqdm

from utils import atomic_write, parse_pages
from utils.pdf_info import detect_pdf_type

_VALID_ANGLES = {90, 180, 270, -90}


def rotate(
    input_path: str | Path,
    output_path: str | Path,
    angle: int,
    pages: str = "all",
    dry_run: bool = False,
) -> None:
    input_path, output_path = str(input_path), str(output_path)

    if angle not in _VALID_ANGLES:
        raise ValueError(
            f"Invalid angle {angle}. Must be one of {sorted(_VALID_ANGLES)}."
        )
    if angle == -90:
        angle = 270

    info = detect_pdf_type(input_path)
    if info.type == "encrypted":
        raise RuntimeError(f"{input_path} is encrypted. Unlock it first.")
    if info.type in ("scanned", "mixed"):
        print(
            "Warning: PDF contains scanned/image pages. "
            "Rotation is visual-only — OCR orientation is not corrected."
        )

    reader = pypdf.PdfReader(input_path)
    page_indices = parse_pages(pages, len(reader.pages))

    if dry_run:
        print(
            f"[dry-run] Would rotate pages {[i + 1 for i in page_indices]} "
            f"by {angle}° → {output_path}"
        )
        return

    writer = pypdf.PdfWriter()
    for i, page in enumerate(tqdm(reader.pages, desc="Rotating", unit="page")):
        writer.add_page(page)
        if i in page_indices:
            writer.pages[i].rotate(angle)

    def _write(tmp: str) -> None:
        with open(tmp, "wb") as f:
            writer.write(f)

    atomic_write(output_path, _write)
    print(f"Rotated {len(page_indices)} page(s) by {angle}° → {output_path}")
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_utils.py -k "rotate" -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add utils/rotate.py tests/test_utils.py
git commit -m "feat: add rotate operation"
```

---

## Task 6: Split — `split.py`

**Files:**
- Modify: `utils/split.py`
- Modify: `tests/test_utils.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_utils.py`**

```python
# ---------------------------------------------------------------------------
# split
# ---------------------------------------------------------------------------

from utils.split import split


def test_split_pages_mode(text_pdf, tmp_path):
    split(str(text_pdf), str(tmp_path), mode="pages")
    files = sorted(tmp_path.glob("*.pdf"))
    assert len(files) == 3
    assert files[0].name == "text_page_001.pdf"
    for f in files:
        assert len(pypdf.PdfReader(str(f)).pages) == 1


def test_split_range_mode(text_pdf, tmp_path):
    split(str(text_pdf), str(tmp_path), mode="range", ranges="1-2,3")
    files = sorted(tmp_path.glob("*.pdf"))
    assert len(files) == 2
    assert len(pypdf.PdfReader(str(files[0])).pages) == 2
    assert len(pypdf.PdfReader(str(files[1])).pages) == 1


def test_split_chunk_mode(text_pdf, tmp_path):
    split(str(text_pdf), str(tmp_path), mode="size", chunk_size=2)
    files = sorted(tmp_path.glob("*.pdf"))
    assert len(files) == 2
    assert len(pypdf.PdfReader(str(files[0])).pages) == 2


def test_split_dry_run(text_pdf, tmp_path):
    split(str(text_pdf), str(tmp_path), mode="pages", dry_run=True)
    assert len(list(tmp_path.glob("*.pdf"))) == 0
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_utils.py::test_split_pages_mode -v
```

Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `utils/split.py`**

```python
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
        if not chunk_size or chunk_size < 1:
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
        out = str(output_dir / name)

        def _write(tmp: str, w: pypdf.PdfWriter = writer) -> None:
            with open(tmp, "wb") as f:
                w.write(f)

        atomic_write(out, _write)

    print(f"Split into {len(groups)} file(s) in {output_dir}")


def _parse_ranges(spec: str, total: int, stem: str) -> tuple[list[list[int]], list[str]]:
    groups: list[list[int]] = []
    names: list[str] = []
    for i, part in enumerate(spec.split(",")):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            group = list(range(int(a) - 1, int(b)))
        else:
            group = [int(part) - 1]
        for idx in group:
            if idx < 0 or idx >= total:
                raise ValueError(
                    f"Page {idx + 1} does not exist — this PDF has {total} pages."
                )
        groups.append(group)
        names.append(f"{stem}_part_{i + 1:03d}.pdf")
    return groups, names
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_utils.py -k "split" -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add utils/split.py tests/test_utils.py
git commit -m "feat: add split operation (pages/range/size modes)"
```

---

## Task 7: Merge — `merge.py`

**Files:**
- Modify: `utils/merge.py`
- Modify: `tests/test_utils.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_utils.py`**

```python
# ---------------------------------------------------------------------------
# merge
# ---------------------------------------------------------------------------

from utils.merge import merge


def test_merge_two_pdfs(two_page_pdf, second_pdf, tmp_path):
    out = str(tmp_path / "merged.pdf")
    merge([str(two_page_pdf), str(second_pdf)], out)
    assert len(pypdf.PdfReader(out).pages) == 4


def test_merge_interleave(two_page_pdf, second_pdf, tmp_path):
    out = str(tmp_path / "interleaved.pdf")
    merge([str(two_page_pdf), str(second_pdf)], out, interleave=True)
    assert len(pypdf.PdfReader(out).pages) == 4
    with pdfplumber.open(out) as pdf:
        assert "First PDF - Page 1" in (pdf.pages[0].extract_text() or "")
        assert "Second PDF - Page A" in (pdf.pages[1].extract_text() or "")


def test_merge_dry_run(two_page_pdf, second_pdf, tmp_path):
    out = str(tmp_path / "dry.pdf")
    merge([str(two_page_pdf), str(second_pdf)], out, dry_run=True)
    assert not os.path.exists(out)
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_utils.py::test_merge_two_pdfs -v
```

Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `utils/merge.py`**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_utils.py -k "merge" -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add utils/merge.py tests/test_utils.py
git commit -m "feat: add merge operation with interleave support"
```

---

## Task 8: Metadata — `metadata.py`

**Files:**
- Modify: `utils/metadata.py`
- Modify: `tests/test_utils.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_utils.py`**

```python
# ---------------------------------------------------------------------------
# metadata
# ---------------------------------------------------------------------------

from utils.metadata import read_metadata, write_metadata


def test_read_metadata(text_pdf):
    meta = read_metadata(str(text_pdf))
    assert isinstance(meta, dict)
    # reportlab always sets /Producer
    assert any("Producer" in k for k in meta)


def test_write_metadata(text_pdf, tmp_path):
    out = str(tmp_path / "meta.pdf")
    write_metadata(str(text_pdf), out, title="Test Title", author="Test Author")
    meta = read_metadata(out)
    assert meta.get("/Title") == "Test Title"
    assert meta.get("/Author") == "Test Author"


def test_write_metadata_dry_run(text_pdf, tmp_path):
    out = str(tmp_path / "meta_dry.pdf")
    write_metadata(str(text_pdf), out, title="Dry", dry_run=True)
    assert not os.path.exists(out)
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_utils.py::test_read_metadata -v
```

Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `utils/metadata.py`**

```python
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
        normalized = f"/{key.capitalize()}" if not key.startswith("/") else key
        existing[normalized] = value
    writer.add_metadata(existing)

    def _write(tmp: str) -> None:
        with open(tmp, "wb") as f:
            writer.write(f)

    atomic_write(output_path, _write)
    print(f"Updated {len(fields)} metadata field(s) → {output_path}")
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_utils.py -k "metadata" -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add utils/metadata.py tests/test_utils.py
git commit -m "feat: add metadata read/write operation"
```

---

## Task 9: Unlock — `unlock.py`

**Files:**
- Modify: `utils/unlock.py`
- Modify: `tests/test_utils.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_utils.py`**

```python
# ---------------------------------------------------------------------------
# unlock
# ---------------------------------------------------------------------------

from utils.unlock import unlock


def test_unlock_with_password(encrypted_pdf, tmp_path):
    out = str(tmp_path / "unlocked.pdf")
    unlock(str(encrypted_pdf), out, password="secret")
    reader = pypdf.PdfReader(out)
    assert not reader.is_encrypted
    assert len(reader.pages) == 3


def test_unlock_wrong_password(encrypted_pdf, tmp_path):
    with pytest.raises(RuntimeError, match="[Ff]ailed|[Ww]rong|[Ii]ncorrect|decrypt"):
        unlock(str(encrypted_pdf), str(tmp_path / "fail.pdf"), password="wrong")


def test_unlock_dry_run(encrypted_pdf, tmp_path):
    out = str(tmp_path / "dry.pdf")
    unlock(str(encrypted_pdf), out, password="secret", dry_run=True)
    assert not os.path.exists(out)
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_utils.py::test_unlock_with_password -v
```

Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `utils/unlock.py`**

```python
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pypdf

from utils import atomic_write
from utils.pdf_info import detect_pdf_type


def unlock(
    input_path: str | Path,
    output_path: str | Path,
    password: str = "",
    dry_run: bool = False,
) -> None:
    input_path, output_path = str(input_path), str(output_path)

    info = detect_pdf_type(input_path)
    if info.type != "encrypted":
        print(f"Note: {input_path} is not encrypted. Copying as-is.")
        if not dry_run:
            shutil.copy2(input_path, output_path)
        return

    print(f"Encryption type: {info.encryption_type}")

    if dry_run:
        print(f"[dry-run] Would decrypt {input_path} → {output_path}")
        return

    # Try pypdf with each candidate password
    for pwd in (["", password] if password else [""]):
        try:
            reader = pypdf.PdfReader(input_path, password=pwd)
            if not reader.is_encrypted:
                _write_decrypted(reader, output_path)
                print(f"Decrypted → {output_path}")
                return
        except Exception:
            pass

    # Fallback: qpdf
    if shutil.which("qpdf"):
        cmd = ["qpdf", "--decrypt"]
        if password:
            cmd += [f"--password={password}"]
        cmd += [input_path, output_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Decrypted via qpdf → {output_path}")
            return
        raise RuntimeError(f"qpdf decryption failed: {result.stderr.strip()}")

    raise RuntimeError(
        "Failed to decrypt: incorrect password or unsupported encryption. "
        "Install qpdf for additional fallback support:\n"
        "  apt: sudo apt-get install qpdf\n"
        "  brew: brew install qpdf\n"
        "  choco: choco install qpdf"
    )


def _write_decrypted(reader: pypdf.PdfReader, output_path: str) -> None:
    writer = pypdf.PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    def _write(tmp: str) -> None:
        with open(tmp, "wb") as f:
            writer.write(f)

    atomic_write(output_path, _write)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_utils.py -k "unlock" -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add utils/unlock.py tests/test_utils.py
git commit -m "feat: add unlock/decrypt operation with qpdf fallback"
```

---

## Task 10: Compress — `compress.py`

**Files:**
- Modify: `utils/compress.py`
- Modify: `tests/test_utils.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_utils.py`**

```python
# ---------------------------------------------------------------------------
# compress
# ---------------------------------------------------------------------------

from utils.compress import compress


def test_compress_text_pdf(text_pdf, tmp_path):
    out = str(tmp_path / "compressed.pdf")
    compress(str(text_pdf), out)
    assert os.path.exists(out)
    assert len(pypdf.PdfReader(out).pages) == 3


def test_compress_invalid_quality(text_pdf, tmp_path):
    with pytest.raises(ValueError, match="quality"):
        compress(str(text_pdf), str(tmp_path / "x.pdf"), quality="ultra")


def test_compress_dry_run(text_pdf, tmp_path):
    out = str(tmp_path / "dry.pdf")
    compress(str(text_pdf), out, dry_run=True)
    assert not os.path.exists(out)
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_utils.py::test_compress_text_pdf -v
```

Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `utils/compress.py`**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_utils.py -k "compress" -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add utils/compress.py tests/test_utils.py
git commit -m "feat: add compress operation (lossless/Ghostscript strategies)"
```

---

## Task 11: Watermark — `watermark.py`

**Files:**
- Modify: `utils/watermark.py`
- Modify: `tests/test_utils.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_utils.py`**

```python
# ---------------------------------------------------------------------------
# watermark
# ---------------------------------------------------------------------------

from utils.watermark import watermark


def test_watermark_text(text_pdf, tmp_path):
    out = str(tmp_path / "watermarked.pdf")
    watermark(str(text_pdf), out, text="CONFIDENTIAL")
    assert len(pypdf.PdfReader(out).pages) == 3


def test_watermark_invalid_opacity(text_pdf, tmp_path):
    with pytest.raises(ValueError, match="opacity"):
        watermark(str(text_pdf), str(tmp_path / "x.pdf"), text="X", opacity=1.5)


def test_watermark_requires_text_or_image(text_pdf, tmp_path):
    with pytest.raises(ValueError, match="text.*image|image.*text|neither"):
        watermark(str(text_pdf), str(tmp_path / "x.pdf"))


def test_watermark_dry_run(text_pdf, tmp_path):
    out = str(tmp_path / "dry.pdf")
    watermark(str(text_pdf), out, text="DRAFT", dry_run=True)
    assert not os.path.exists(out)
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_utils.py::test_watermark_text -v
```

Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `utils/watermark.py`**

```python
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
        raise ValueError(
            "Provide either --text or --image (not neither)."
        )
    if not (0.0 <= opacity <= 1.0):
        raise ValueError(
            f"opacity must be 0.0–1.0, got {opacity}."
        )

    info = detect_pdf_type(input_path)
    if info.type == "encrypted":
        raise RuntimeError(f"{input_path} is encrypted. Unlock it first.")
    if info.type in ("scanned", "mixed"):
        print("Note: watermark is added as a vector overlay on scanned pages.")

    reader = pypdf.PdfReader(input_path)
    page_indices = parse_pages(pages, len(reader.pages))

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
                _text_watermark(text, w, h, font_size, opacity, color)  # type: ignore[arg-type]
                if text
                else _image_watermark(image, w, h, position, scale, opacity)  # type: ignore[arg-type]
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
    if position not in coords:
        raise ValueError(
            f"Invalid position '{position}'. Use: center, top-right, bottom-left."
        )
    x, y = coords[position]

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(w, h))
    c.setFillAlpha(opacity)
    c.drawImage(image_path, x, y, width=draw_w, height=draw_h, mask="auto")
    c.save()
    buf.seek(0)
    return buf
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_utils.py -k "watermark" -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add utils/watermark.py tests/test_utils.py
git commit -m "feat: add watermark operation (text diagonal, image overlay)"
```

---

## Task 12: Extract — `extract.py`

**Files:**
- Modify: `utils/extract.py`
- Modify: `tests/test_utils.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_utils.py`**

```python
# ---------------------------------------------------------------------------
# extract
# ---------------------------------------------------------------------------

import glob as _glob

from utils.extract import extract


def test_extract_text(text_pdf, tmp_path):
    out = str(tmp_path / "extracted.txt")
    extract(str(text_pdf), out, type_="text")
    assert os.path.exists(out)
    assert "Hello, PDF toolkit!" in Path(out).read_text()


def test_extract_pages_as_images(text_pdf, tmp_path):
    pytest.importorskip("pdf2image")
    out_dir = str(tmp_path / "pages")
    extract(str(text_pdf), out_dir, type_="pages")
    pngs = _glob.glob(os.path.join(out_dir, "*.png"))
    assert len(pngs) == 3


def test_extract_invalid_type(text_pdf, tmp_path):
    with pytest.raises(ValueError, match="type"):
        extract(str(text_pdf), str(tmp_path / "x"), type_="video")


def test_extract_dry_run(text_pdf, tmp_path):
    out = str(tmp_path / "dry.txt")
    extract(str(text_pdf), out, type_="text", dry_run=True)
    assert not os.path.exists(out)
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_utils.py::test_extract_text -v
```

Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `utils/extract.py`**

```python
from __future__ import annotations

import csv
import os
import shutil
import subprocess
from pathlib import Path

import pdfplumber
import pypdf
from tqdm import tqdm

from utils import atomic_write, parse_pages
from utils.pdf_info import detect_pdf_type

_VALID_TYPES = {"text", "images", "tables", "pages"}


def extract(
    input_path: str | Path,
    output_path: str | Path,
    type_: str = "text",
    pages: str = "all",
    dry_run: bool = False,
) -> None:
    input_path, output_path = str(input_path), str(output_path)

    if type_ not in _VALID_TYPES:
        raise ValueError(
            f"Invalid type '{type_}'. Choose from: {sorted(_VALID_TYPES)}"
        )

    info = detect_pdf_type(input_path)
    if info.type == "encrypted":
        raise RuntimeError(f"{input_path} is encrypted. Unlock it first.")

    reader = pypdf.PdfReader(input_path)
    page_indices = parse_pages(pages, len(reader.pages))

    if dry_run:
        print(
            f"[dry-run] Would extract {type_} from "
            f"{len(page_indices)} page(s) → {output_path}"
        )
        return

    if type_ == "text":
        _extract_text(input_path, output_path, page_indices, info)
    elif type_ == "images":
        _extract_images(input_path, output_path, page_indices, reader)
    elif type_ == "tables":
        _extract_tables(input_path, output_path, page_indices)
    elif type_ == "pages":
        _extract_pages(input_path, output_path, page_indices)


def _extract_text(
    input_path: str, output_path: str, page_indices: list[int], info
) -> None:
    if info.type in ("scanned", "mixed"):
        print(
            "Warning: scanned PDF detected. "
            "Falling back to OCR (requires tesseract + pdf2image)."
        )
        _ocr_text(input_path, output_path, page_indices)
        return

    lines: list[str] = []
    with pdfplumber.open(input_path) as pdf:
        for i in tqdm(page_indices, desc="Extracting text", unit="page"):
            text = pdf.pages[i].extract_text() or ""
            lines.append(f"--- Page {i + 1} ---\n{text}\n")

    def _write(tmp: str) -> None:
        Path(tmp).write_text("\n".join(lines), encoding="utf-8")

    atomic_write(output_path, _write)
    print(f"Extracted text from {len(page_indices)} page(s) → {output_path}")


def _ocr_text(
    input_path: str, output_path: str, page_indices: list[int]
) -> None:
    if not shutil.which("tesseract"):
        raise RuntimeError(
            "tesseract not found.\n"
            "Install:  apt: tesseract-ocr | brew: tesseract | choco: tesseract"
        )
    from pdf2image import convert_from_path
    import pytesseract

    images = convert_from_path(input_path)
    lines: list[str] = []
    for i in tqdm(page_indices, desc="OCR", unit="page"):
        text = pytesseract.image_to_string(images[i])
        lines.append(f"--- Page {i + 1} (OCR) ---\n{text}\n")

    def _write(tmp: str) -> None:
        Path(tmp).write_text("\n".join(lines), encoding="utf-8")

    atomic_write(output_path, _write)
    print(f"OCR extracted {len(page_indices)} page(s) → {output_path}")


def _extract_images(
    input_path: str, output_path: str,
    page_indices: list[int], reader: pypdf.PdfReader,
) -> None:
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    if shutil.which("pdfimages"):
        subprocess.run(
            ["pdfimages", "-png", input_path, str(out_dir / "img")],
            check=True,
        )
        print(f"Extracted images → {out_dir}")
        return

    count = 0
    for i in tqdm(page_indices, desc="Extracting images", unit="page"):
        for j, img in enumerate(reader.pages[i].images):
            ext = img.name.split(".")[-1].lower() if "." in img.name else "png"
            dest = out_dir / f"page_{i + 1:03d}_img_{j + 1:03d}.{ext}"
            dest.write_bytes(img.data)
            count += 1
    print(f"Extracted {count} image(s) → {out_dir}")


def _extract_tables(
    input_path: str, output_path: str, page_indices: list[int]
) -> None:
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    with pdfplumber.open(input_path) as pdf:
        for i in tqdm(page_indices, desc="Extracting tables", unit="page"):
            for j, table in enumerate(pdf.pages[i].extract_tables()):
                dest = out_dir / f"page_{i + 1:03d}_table_{j + 1:03d}.csv"
                with open(dest, "w", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerows(table)
                count += 1
    print(f"Extracted {count} table(s) → {out_dir}")


def _extract_pages(
    input_path: str, output_path: str, page_indices: list[int]
) -> None:
    from pdf2image import convert_from_path

    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    images = convert_from_path(input_path)
    for i in tqdm(page_indices, desc="Rendering pages", unit="page"):
        images[i].save(str(out_dir / f"page_{i + 1:03d}.png"), "PNG")
    print(f"Exported {len(page_indices)} page(s) as PNG → {out_dir}")
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_utils.py -k "extract" -v
```

Expected: all 4 tests PASS (pages test skipped if pdf2image unavailable).

- [ ] **Step 5: Commit**

```bash
git add utils/extract.py tests/test_utils.py
git commit -m "feat: add extract operation (text/images/tables/pages)"
```

---

## Task 13: Crop — `crop.py`

**Files:**
- Modify: `utils/crop.py`
- Modify: `tests/test_utils.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_utils.py`**

```python
# ---------------------------------------------------------------------------
# crop
# ---------------------------------------------------------------------------

from utils.crop import crop, parse_box


def test_parse_box_valid():
    assert parse_box("50,50,500,700") == (50.0, 50.0, 500.0, 700.0)


def test_parse_box_invalid():
    with pytest.raises(ValueError, match="box"):
        parse_box("50,50,500")  # only 3 values


def test_crop_cli_mode(text_pdf, tmp_path):
    out = str(tmp_path / "cropped.pdf")
    crop(str(text_pdf), out, box="50,50,500,700", pages="all")
    reader = pypdf.PdfReader(out)
    assert len(reader.pages) == 3
    cb = reader.pages[0].cropbox
    assert float(cb.left) == 50.0
    assert float(cb.bottom) == 50.0


def test_crop_dry_run(text_pdf, tmp_path):
    out = str(tmp_path / "dry.pdf")
    crop(str(text_pdf), out, box="50,50,500,700", dry_run=True)
    assert not os.path.exists(out)


def test_crop_requires_box_or_gui(text_pdf, tmp_path):
    with pytest.raises(ValueError, match="box.*gui|gui.*box|--box|--gui"):
        crop(str(text_pdf), str(tmp_path / "x.pdf"))
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_utils.py::test_parse_box_valid -v
```

Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `utils/crop.py`**

```python
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
    writer = pypdf.PdfWriter()
    for i, page in enumerate(tqdm(reader.pages, desc="Cropping", unit="page")):
        writer.add_page(page)
        if i in page_indices:
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_utils.py -k "crop or parse_box" -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add utils/crop.py tests/test_utils.py
git commit -m "feat: add crop operation with CLI box and tkinter GUI"
```

---

## Task 14: CLI Entry Point — `main.py`

**Files:**
- Create: `main.py`

- [ ] **Step 1: Write `main.py`**

```python
#!/usr/bin/env python3
"""PDF Toolkit — CLI entry point."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _default_output(input_path: str, operation: str, ext: str = ".pdf") -> str:
    p = Path(input_path)
    return str(p.parent / f"{p.stem}_{operation}{ext}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pdf-toolkit",
        description="Python PDF editing toolkit",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # compress
    p = sub.add_parser("compress", help="Compress a PDF")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument(
        "--quality",
        choices=["screen", "ebook", "printer", "prepress"],
        default="printer",
    )
    p.add_argument("--dry-run", action="store_true")

    # crop
    p = sub.add_parser("crop", help="Crop pages")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument("--box", help="x1,y1,x2,y2 in PDF points")
    p.add_argument("--pages", default="all")
    p.add_argument("--gui", action="store_true")
    p.add_argument("--dry-run", action="store_true")

    # rotate
    p = sub.add_parser("rotate", help="Rotate pages")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument("--angle", type=int, required=True, choices=[90, 180, 270, -90])
    p.add_argument("--pages", default="all")
    p.add_argument("--dry-run", action="store_true")

    # unlock
    p = sub.add_parser("unlock", help="Remove password protection")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument("--password", default="")
    p.add_argument("--dry-run", action="store_true")

    # split
    p = sub.add_parser("split", help="Split PDF into parts")
    p.add_argument("input")
    p.add_argument("--output-dir")
    p.add_argument(
        "--mode", choices=["pages", "range", "size"], default="pages"
    )
    p.add_argument("--ranges")
    p.add_argument("--chunk-size", type=int)
    p.add_argument("--dry-run", action="store_true")

    # merge
    p = sub.add_parser("merge", help="Merge PDFs")
    p.add_argument("inputs", nargs="+")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--interleave", action="store_true")
    p.add_argument("--dry-run", action="store_true")

    # watermark
    p = sub.add_parser("watermark", help="Add watermark")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument("--text")
    p.add_argument("--image")
    p.add_argument("--font-size", type=int, default=48)
    p.add_argument("--opacity", type=float, default=0.3)
    p.add_argument("--color", default="#FF0000")
    p.add_argument(
        "--position",
        choices=["center", "top-right", "bottom-left"],
        default="center",
    )
    p.add_argument("--scale", type=float, default=0.2)
    p.add_argument("--pages", default="all")
    p.add_argument("--dry-run", action="store_true")

    # extract
    p = sub.add_parser("extract", help="Extract content")
    p.add_argument("input")
    p.add_argument(
        "--type",
        dest="type_",
        choices=["text", "images", "tables", "pages"],
        default="text",
    )
    p.add_argument("--output")
    p.add_argument("--pages", default="all")
    p.add_argument("--dry-run", action="store_true")

    # metadata
    p = sub.add_parser("metadata", help="Read or edit PDF metadata")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument("--read", action="store_true")
    p.add_argument("--set", nargs="+", metavar="key=value", dest="fields")
    p.add_argument("--dry-run", action="store_true")

    # info
    p = sub.add_parser("info", help="Detect PDF type and show info")
    p.add_argument("input")

    args = parser.parse_args()
    try:
        _dispatch(args)
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def _dispatch(args: argparse.Namespace) -> None:
    cmd = args.command

    if cmd == "compress":
        from utils.compress import compress
        out = args.output or _default_output(args.input, "compressed")
        compress(args.input, out, quality=args.quality, dry_run=args.dry_run)

    elif cmd == "crop":
        from utils.crop import crop
        out = args.output or _default_output(args.input, "cropped")
        crop(
            args.input, out,
            box=args.box, pages=args.pages,
            gui=args.gui, dry_run=args.dry_run,
        )

    elif cmd == "rotate":
        from utils.rotate import rotate
        out = args.output or _default_output(args.input, "rotated")
        rotate(
            args.input, out,
            angle=args.angle, pages=args.pages, dry_run=args.dry_run,
        )

    elif cmd == "unlock":
        from utils.unlock import unlock
        out = args.output or _default_output(args.input, "unlocked")
        unlock(args.input, out, password=args.password, dry_run=args.dry_run)

    elif cmd == "split":
        from utils.split import split
        out_dir = args.output_dir or str(Path(args.input).parent)
        split(
            args.input, out_dir,
            mode=args.mode, ranges=args.ranges,
            chunk_size=args.chunk_size, dry_run=args.dry_run,
        )

    elif cmd == "merge":
        from utils.merge import merge
        merge(
            args.inputs, args.output,
            interleave=args.interleave, dry_run=args.dry_run,
        )

    elif cmd == "watermark":
        from utils.watermark import watermark
        out = args.output or _default_output(args.input, "watermarked")
        watermark(
            args.input, out,
            text=args.text, image=args.image,
            font_size=args.font_size, opacity=args.opacity,
            color=args.color, position=args.position,
            scale=args.scale, pages=args.pages,
            dry_run=args.dry_run,
        )

    elif cmd == "extract":
        from utils.extract import extract
        ext = ".txt" if args.type_ == "text" else ""
        out = args.output or _default_output(
            args.input, f"extracted_{args.type_}", ext
        )
        extract(
            args.input, out,
            type_=args.type_, pages=args.pages, dry_run=args.dry_run,
        )

    elif cmd == "metadata":
        from utils.metadata import read_metadata, write_metadata
        if args.read or not args.fields:
            for k, v in read_metadata(args.input).items():
                print(f"  {k}: {v}")
        if args.fields:
            out = args.output or _default_output(args.input, "meta")
            parsed: dict[str, str] = {}
            for item in args.fields:
                if "=" not in item:
                    raise ValueError(
                        f"Invalid --set format '{item}'. Use key=value."
                    )
                k, v = item.split("=", 1)
                parsed[k] = v
            write_metadata(
                args.input, out, dry_run=args.dry_run, **parsed
            )

    elif cmd == "info":
        from utils.pdf_info import detect_pdf_type
        info = detect_pdf_type(args.input)
        print(f"File:         {args.input}")
        print(f"Type:         {info.type}")
        print(f"Pages:        {info.page_count}")
        print(f"Encrypted:    {info.encryption_type or 'No'}")
        print(f"Has forms:    {info.has_forms}")
        print(f"Text pages:   {info.text_page_count}")
        print(f"Image pages:  {info.image_only_page_count}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify help output**

```bash
cd /home/ubuntu/myRepo/repo/pdf-toolkit
python main.py --help
```

Expected: lists all subcommands (compress, crop, rotate, unlock, split, merge, watermark, extract, metadata, info).

- [ ] **Step 3: Smoke test**

```bash
python -c "
from reportlab.pdfgen import canvas
c = canvas.Canvas('/tmp/smoke.pdf')
c.drawString(100, 700, 'Smoke test PDF')
c.save()
"
python main.py info /tmp/smoke.pdf
```

Expected: prints type=text, pages=1, encrypted=No.

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat: add CLI entry point with all subcommands"
```

---

## Task 15: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`**

```markdown
# PDF Toolkit

A Python CLI for editing PDF files. Supports compression, cropping, rotation,
unlocking, splitting, merging, watermarking, metadata editing, and content extraction.

## Installation

### Python packages

```bash
pip install -r requirements.txt
```

### System packages

| Tool | Purpose | Linux (apt) | macOS (brew) | Windows (choco) |
|---|---|---|---|---|
| ghostscript | Image compression | `sudo apt-get install ghostscript` | `brew install ghostscript` | `choco install ghostscript` |
| qpdf | Lossless compression, decrypt fallback | `sudo apt-get install qpdf` | `brew install qpdf` | `choco install qpdf` |
| poppler-utils | Image extraction (`pdfimages`) | `sudo apt-get install poppler-utils` | `brew install poppler` | `choco install poppler` |
| tesseract-ocr | OCR on scanned PDFs | `sudo apt-get install tesseract-ocr` | `brew install tesseract` | `choco install tesseract` |

## Quick Start

```bash
python main.py info document.pdf
python main.py compress document.pdf -o compressed.pdf
python main.py rotate document.pdf -o rotated.pdf --angle 90
```

## Usage Reference

### info — Detect PDF type

```bash
python main.py info input.pdf
```

### compress — Reduce file size

```bash
python main.py compress input.pdf -o output.pdf --quality printer
# --quality: screen (72 dpi) | ebook (150 dpi) | printer (300 dpi, default) | prepress (lossless)
python main.py compress input.pdf --dry-run
```

### crop — Trim page margins

```bash
# CLI mode: box is x1,y1,x2,y2 in PDF points (1 pt = 1/72 inch)
python main.py crop input.pdf -o output.pdf --box "50,50,500,700" --pages all
python main.py crop input.pdf -o output.pdf --box "50,50,500,700" --pages "1,3-5"

# GUI mode: opens a tkinter window to draw the crop box visually
python main.py crop input.pdf --gui
```

### rotate — Rotate pages

```bash
python main.py rotate input.pdf -o output.pdf --angle 90 --pages all
python main.py rotate input.pdf -o output.pdf --angle 180 --pages "1,3"
python main.py rotate input.pdf -o output.pdf --angle 270 --pages "2-5"
python main.py rotate input.pdf -o output.pdf --angle -90  # counter-clockwise
```

### unlock — Remove password protection

```bash
python main.py unlock input.pdf -o output.pdf --password "secret"
python main.py unlock input.pdf -o output.pdf  # tries empty password first
```

### split — Split into parts

```bash
# One file per page (default)
python main.py split input.pdf --output-dir ./pages/

# By page ranges
python main.py split input.pdf --mode range --ranges "1-3,4-6,7" --output-dir ./parts/

# By chunk size
python main.py split input.pdf --mode size --chunk-size 10 --output-dir ./chunks/
```

### merge — Combine PDFs

```bash
python main.py merge file1.pdf file2.pdf file3.pdf -o merged.pdf

# Interleave pages from two files (useful for double-sided scans)
python main.py merge front.pdf back.pdf -o interleaved.pdf --interleave
```

### watermark — Add text or image overlay

```bash
# Diagonal text watermark
python main.py watermark input.pdf -o output.pdf --text "CONFIDENTIAL"
python main.py watermark input.pdf -o output.pdf --text "DRAFT" --opacity 0.2 --color "#0000FF" --font-size 60

# Image watermark
python main.py watermark input.pdf -o output.pdf --image logo.png --position top-right --scale 0.15
# --position: center | top-right | bottom-left
```

### extract — Extract content

```bash
# Text (falls back to OCR for scanned PDFs)
python main.py extract input.pdf --type text --output extracted.txt

# Embedded images
python main.py extract input.pdf --type images --output ./images/

# Tables as CSV
python main.py extract input.pdf --type tables --output ./tables/

# Pages as PNG
python main.py extract input.pdf --type pages --output ./png-pages/
```

### metadata — Read or edit PDF metadata

```bash
python main.py metadata input.pdf --read
python main.py metadata input.pdf -o output.pdf --set title="My Document" author="Jane Doe"
python main.py metadata input.pdf -o output.pdf --set title="Report" subject="Q4 Results"
```

## Compatibility

| Feature | Text PDF | Scanned PDF | Encrypted PDF | Forms |
|---|---|---|---|---|
| compress | ✅ lossless | ✅ Ghostscript | ❌ unlock first | ✅ |
| crop | ✅ | ✅ | ❌ unlock first | ✅ |
| rotate | ✅ | ⚠️ visual only | ❌ unlock first | ✅ |
| unlock | — | — | ✅ | — |
| split | ✅ | ✅ | ❌ unlock first | ✅ |
| merge | ✅ | ✅ | ❌ unlock first | ✅ |
| watermark | ✅ | ⚠️ vector overlay | ❌ unlock first | ✅ |
| extract text | ✅ | ⚠️ OCR fallback | ❌ unlock first | ✅ |
| extract images | ✅ | ✅ | ❌ unlock first | ✅ |
| extract tables | ✅ | ❌ | ❌ unlock first | ✅ |
| metadata | ✅ | ✅ | ❌ unlock first | ✅ |

## Troubleshooting

**Ghostscript not found**

The `compress` command falls back to pypdf-only for text PDFs. For image/mixed PDFs, install ghostscript:

```bash
sudo apt-get install ghostscript       # Linux
brew install ghostscript               # macOS
choco install ghostscript              # Windows
```

**Tesseract language pack missing**

```bash
sudo apt-get install tesseract-ocr-eng  # English (default)
sudo apt-get install tesseract-ocr-ara  # Arabic
# See: https://github.com/tesseract-ocr/tessdata
```

**tkinter not available**

```bash
sudo apt-get install python3-tk                 # Linux
brew install python-tk@3.12                     # macOS (match your Python version)
# Windows: reinstall Python and check "tcl/tk and IDLE" checkbox
```

**pdfplumber / pypdf version conflict**

```bash
pip install --upgrade pypdf pdfplumber
```

**qpdf decrypt fails**

Try providing the password explicitly with `--password`. If unknown, some tools like `pdfcrack` can recover weak passwords.
```

- [ ] **Step 2: Run the full test suite**

```bash
cd /home/ubuntu/myRepo/repo/pdf-toolkit
pytest tests/ -v
```

Expected: all tests PASS (external-tool-dependent tests skip gracefully if tools absent).

- [ ] **Step 3: Final commit**

```bash
git add README.md
git commit -m "docs: add README with full usage reference, compatibility table, troubleshooting"
```

---

## Self-Review

### Spec Coverage

| Spec requirement | Task |
|---|---|
| `parse_pages()` in `utils/__init__.py` | Task 3 |
| `atomic_write()` in `utils/__init__.py` | Task 3 |
| `PDFInfo` dataclass + `detect_pdf_type()` | Task 4 |
| `compress` — lossless for text, Ghostscript for image, pypdf fallback | Task 10 |
| `compress` — print before/after sizes and ratio | Task 10 |
| `crop` — CLI `--box` mode | Task 13 |
| `crop` — tkinter GUI drag-select with coordinate display | Task 13 |
| `rotate` — angle validation, scanned warning | Task 5 |
| `unlock` — empty password attempt, qpdf fallback, encryption type display | Task 9 |
| `split` — pages/range/size modes | Task 6 |
| `merge` — interleave support | Task 7 |
| `watermark` — diagonal text (font-size, opacity, color) | Task 11 |
| `watermark` — image overlay (position, scale) | Task 11 |
| `metadata` — read + write | Task 8 |
| `extract text` — pdfplumber + OCR fallback | Task 12 |
| `extract images/tables/pages` | Task 12 |
| `main.py` — all subcommands + universal flags | Task 14 |
| `--dry-run` on every operation | Tasks 5–13 |
| `tqdm` progress bars on multi-page operations | Tasks 5–13 |
| External tool detection + install instructions | Tasks 9, 10, 12, 13 |
| `requirements.txt` | Task 1 |
| `README.md` — install, usage, compatibility, troubleshooting | Task 15 |
| `tests/conftest.py` — session-scoped PDF fixtures | Task 2 |
| `tests/test_utils.py` — covers all modules | Tasks 3–13 |

All spec requirements covered. No gaps found.
