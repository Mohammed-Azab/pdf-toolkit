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
        if not part:
            raise ValueError(f"Invalid page spec '{spec}': empty token.")
        if "-" in part:
            halves = part.split("-", 1)
            try:
                start, end = int(halves[0]), int(halves[1])
            except ValueError:
                raise ValueError(f"Invalid page range '{part}' in spec '{spec}'.")
            if end < start:
                raise ValueError(
                    f"Invalid page range '{part}': end page must be >= start page."
                )
            for n in range(start, end + 1):
                _check_page(n, total)
                indices.append(n - 1)
        else:
            try:
                n = int(part)
            except ValueError:
                raise ValueError(f"Invalid page number '{part}' in spec '{spec}'.")
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
