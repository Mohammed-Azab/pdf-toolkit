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
