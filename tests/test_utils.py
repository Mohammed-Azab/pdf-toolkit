import os
import shutil
from pathlib import Path

import pdfplumber
import pypdf
import pytest

from utils import atomic_write, parse_pages
from utils.pdf_info import PDFInfo, detect_pdf_type


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


# ---------------------------------------------------------------------------
# pdf_info
# ---------------------------------------------------------------------------

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
