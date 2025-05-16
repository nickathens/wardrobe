"""Minimal ``secure_filename`` replacement used when Werkzeug is missing."""

from __future__ import annotations

import re

_invalid = re.compile(r"[^A-Za-z0-9_.-]")


def secure_filename(name: str) -> str:
    """Sanitize ``name`` to avoid unsafe file paths.

    The implementation rejects path separators and strips characters that are
    not alphanumerics, ``.``, ``_`` or ``-``.
    """

    if '/' in name or '\\' in name or name.startswith('..') or '\x00' in name:
        raise ValueError("invalid filename")
    return _invalid.sub("", name)
