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

    # Try pypdf using reader.decrypt() which returns a PasswordType enum.
    # PasswordType.NOT_DECRYPTED means the password was wrong; anything else is success.
    for pwd in (["", password] if password else [""]):
        try:
            reader = pypdf.PdfReader(input_path)
            result = reader.decrypt(pwd)
            if result != pypdf.PasswordType.NOT_DECRYPTED:
                _write_decrypted(reader, output_path)
                print(f"Decrypted → {output_path}")
                return
        except (pypdf.errors.PdfReadError, NotImplementedError):
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
