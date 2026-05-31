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
