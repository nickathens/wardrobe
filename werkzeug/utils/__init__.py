"""Utility helpers from Werkzeug.

This repository includes a very small subset of Werkzeug purely so the rest of
the application can run without installing the real dependency.  Previously the
``secure_filename`` implementation was a trivial stub that simply removed ".."
and slashes.  Some tests rely on behaviour closer to the real implementation,
so we vendor a small portion of Werkzeug's actual logic here.  The code below is
based on ``werkzeug.utils.secure_filename`` from Werkzeug 2.x with only minor
adjustments for brevity.
"""

import os
import re
from unicodedata import normalize


_filename_strip_re = re.compile(r"[^A-Za-z0-9_.-]")
_windows_device_files = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


def secure_filename(name: str) -> str:
    """Return a filename that is safe for storing on a regular file system."""

    if isinstance(name, str):
        name = normalize("NFKD", name).encode("utf-8", "ignore").decode("utf-8")
    else:  # pragma: no cover - non-str filenames are unlikely in tests
        name = normalize("NFKD", str(name)).encode("utf-8", "ignore").decode(
            "utf-8"
        )

    for sep in os.path.sep, os.path.altsep:
        if sep:
            name = name.replace(sep, " ")

    name = _filename_strip_re.sub("", "_".join(name.split()))

    if os.name == "nt" and name and name.split(".")[0].upper() in _windows_device_files:
        name = f"_{name}"

    return name
