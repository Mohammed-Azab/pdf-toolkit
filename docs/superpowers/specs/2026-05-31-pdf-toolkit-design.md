# PDF Toolkit — Design Spec
**Date:** 2026-05-31  
**Status:** Approved

---

## 1. Overview

A Python CLI toolkit for editing PDF files, structured as a single `pdf-toolkit/` directory. The entry point is `main.py` (argparse subcommands); each operation lives in a focused `utils/` module. Every operation calls `pdf_info.py` first to detect PDF type and gate behavior accordingly.

---

## 2. Repository Layout

```
pdf-toolkit/
├── main.py                   # CLI entry point
├── requirements.txt
├── README.md
├── utils/
│   ├── __init__.py           # shared helpers: parse_pages(), atomic_write()
│   ├── compress.py
│   ├── crop.py               # tkinter GUI for visual crop selection
│   ├── rotate.py
│   ├── unlock.py
│   ├── split.py
│   ├── merge.py
│   ├── watermark.py
│   ├── metadata.py
│   ├── extract.py
│   └── pdf_info.py
└── tests/
    └── test_utils.py
```

---

## 3. Architecture

### 3.1 CLI Dispatcher (`main.py`)

- Uses `argparse` with subcommands; each subcommand delegates to one util module.
- Universal flags on every subcommand:
  - `-o / --output` — output path; default: `<input>_<operation>.pdf`
  - `--pages` — range syntax: `1`, `1,3`, `2-5`, `all` (default: `all`)
  - `--dry-run` — print what would happen, write nothing
- No logic lives in `main.py` beyond argument parsing and dispatch.

### 3.2 Shared Utilities (`utils/__init__.py`)

Two helpers used by every module:

**`parse_pages(spec: str, total: int) -> list[int]`**  
Converts `"1"`, `"1,3"`, `"2-5"`, `"all"` into a sorted zero-indexed list. Raises `ValueError` with the page count if a page is out of range.

**`atomic_write(path: str, writer_fn: Callable[[str], None]) -> None`**  
Writes to `path + ".tmp"` then calls `os.replace()`. Guarantees the original is never partially overwritten.

---

## 4. Module Specifications

### 4.1 `pdf_info.py` — Type Detection

Returns a `PDFInfo` dataclass:

```python
@dataclass
class PDFInfo:
    type: Literal["text", "scanned", "mixed", "form", "encrypted"]
    page_count: int
    encryption_type: str | None   # e.g. "AES-256", "RC4-128"
    has_forms: bool
    text_page_count: int
    image_only_page_count: int
```

**Detection logic:**
1. Open with `pypdf`; if encrypted → return `type="encrypted"` immediately.
2. Check `pypdf` AcroForm fields → set `has_forms`.
3. For each page, use `pdfplumber` to extract text. If text length > threshold → text page; else if page has images → scanned page.
4. Classify overall type: all text → `"text"`; all scanned → `"scanned"`; mix → `"mixed"`; has forms → `"form"`.

**Used by:** every other module at the top of its main function; warns the user if the type is incompatible with the requested operation.

---

### 4.2 `compress.py`

**Strategy selection:**
- `type="text"` → pypdf lossless pipeline (`compress_identical_objects()` + `compress_content_streams()`), then qpdf linearize via subprocess.
- `type="scanned"` or `"mixed"` → Ghostscript subprocess with `-dPDFSETTINGS`.
- If Ghostscript absent → pypdf-only fallback + warning.

**Quality presets (Ghostscript):**
| Flag | `-dPDFSETTINGS` | DPI |
|---|---|---|
| `screen` | `/screen` | 72 |
| `ebook` | `/ebook` | 150 |
| `printer` | `/printer` | 300 (default) |
| `prepress` | `/prepress` | lossless |

**Output:** prints before/after sizes and compression ratio on completion.

---

### 4.3 `crop.py`

**CLI mode:**  
`--box "x1,y1,x2,y2"` in PDF points. Applies `page.cropbox = RectangleObject([x1,y1,x2,y2])` via pypdf to selected pages.

**GUI mode (`--gui`):**
1. Render first page (or `--page N`) to PIL Image via `pdf2image`.
2. Display in a `tkinter.Canvas`.
3. User draws rectangle via click-drag; live coordinate display (in PDF points) updates as they drag.
4. Buttons: **Apply to this page** / **Apply to all pages** / **Cancel**.
5. Pixel → PDF point conversion: `pt = px * (mediabox_width_pts / canvas_width_px)`.

---

### 4.4 `rotate.py`

- Angles: `90`, `180`, `270` (clockwise), `-90` (counter-clockwise, converted to `270`).
- Uses `pypdf` `page.rotate(angle)`.
- Warns if PDF is scanned: rotation is visual-only, OCR orientation is not corrected.

---

### 4.5 `unlock.py`

1. Try `pypdf.PdfReader(path, password="")` (empty password).
2. If that fails and `--password` provided, try supplied password.
3. On success, write decrypted PDF with `PdfWriter`.
4. If pypdf fails, fall back to `qpdf --decrypt` subprocess.
5. Prints encryption type (from `pdf_info.py`) before attempting.

---

### 4.6 `split.py`

Three modes via `--mode`:
- `pages` (default): one PDF per page → `<stem>_page_001.pdf`, `_002.pdf`, etc.
- `range`: split by explicit ranges `--ranges "1-3,4-6,7"` → one PDF per range group.
- `size`: `--chunk-size N` → consecutive N-page chunks.

All output files go to `--output-dir` (default: directory of input file).

---

### 4.7 `merge.py`

- Accepts 2+ positional input paths.
- `--interleave`: zip pages from exactly two PDFs (front/back of double-sided scan).
- Preserves outlines/bookmarks from all inputs using `pypdf` outline copying.

---

### 4.8 `watermark.py`

**Text watermark (`--text`):**
- `reportlab` generates an in-memory PDF with diagonal text at 45°.
- Options: `--font-size` (default 48), `--opacity` (0.0–1.0, default 0.3), `--color` hex (default `#FF0000`).
- Merged over each page with `pypdf` `page.merge_page()`.

**Image watermark (`--image`):**
- `reportlab` places the image at the specified `--position` (center/top-right/bottom-left) scaled by `--scale` (0.0–1.0, default 0.2).
- Same merge approach.

---

### 4.9 `metadata.py`

- `--read`: print all standard fields (Title, Author, Subject, Creator, Producer, CreationDate, ModDate) plus any custom fields.
- `--set key=value ...`: update the `pypdf` `PdfWriter` metadata dict then write atomically.

---

### 4.10 `extract.py`

| `--type` | Tool | Output |
|---|---|---|
| `text` | `pdfplumber` | `.txt`, layout-preserving |
| `text` (scanned) | `pytesseract` + `pdf2image` | `.txt`, with OCR warning |
| `images` | `pypdf` XObject extraction or `pdfimages` subprocess | files in output dir |
| `tables` | `pdfplumber` | one `.csv` per table |
| `pages` | `pdf2image` | one `.png` per page |

---

## 5. Cross-Cutting Concerns

### 5.1 External Tool Detection

At the top of each module that calls an external tool, detect presence with `shutil.which()`. If missing, print install instructions for apt/brew/choco and raise `RuntimeError` with actionable message.

### 5.2 Progress Bars

All multi-page loops use `tqdm`. Single-file operations do not.

### 5.3 Atomic Writes

All file outputs go through `utils.atomic_write()`. Temp file is written alongside the target (same filesystem), then `os.replace()` is called.

### 5.4 Error Messages

Exceptions include context: `"Page 7 does not exist — this PDF has 5 pages."` File-not-found errors print the full path. Missing password errors distinguish between wrong-password and no-password-provided.

### 5.5 Dry Run

`--dry-run` prints a summary of what would happen (pages affected, output path, estimated output) and exits without writing anything.

---

## 6. Dependencies

**Python packages (`requirements.txt`):**
```
pypdf>=4.0.0
pdfplumber>=0.10.0
reportlab>=4.0.0
pdf2image>=1.17.0
Pillow>=10.0.0
pytesseract>=0.3.10
tqdm>=4.0.0
```

**System packages:**
| Tool | Purpose | apt | brew | choco |
|---|---|---|---|---|
| `ghostscript` | Image compression | `ghostscript` | `ghostscript` | `ghostscript` |
| `qpdf` | Lossless compression, decrypt fallback | `qpdf` | `qpdf` | `qpdf` |
| `poppler-utils` | `pdfimages`, `pdftotext` | `poppler-utils` | `poppler` | `poppler` |
| `tesseract-ocr` | OCR on scanned PDFs | `tesseract-ocr` | `tesseract` | `tesseract` |

---

## 7. Testing (`tests/test_utils.py`)

- Synthetic 3-page PDF fixture created with `reportlab` at test session start (one text page, one image page, one mixed page).
- Tests cover: `parse_pages()`, `pdf_info` type detection, `rotate`, `split` (all 3 modes), `merge`, `metadata` read/write, `watermark` text mode.
- Tests that require external tools (`ghostscript`, `tesseract`, `qpdf`) are skipped with `pytest.mark.skipif(shutil.which(...) is None)`.

---

## 8. README Sections

1. Installation (pip + system packages for apt/brew/choco)
2. Quick start
3. Full usage reference (every subcommand + all flags)
4. Compatibility table (text / scanned / encrypted / forms)
5. Troubleshooting (ghostscript not found, tesseract language pack, tkinter unavailable)
