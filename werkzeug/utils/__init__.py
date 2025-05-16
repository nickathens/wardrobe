"""Compatibility wrapper for :mod:`werkzeug.utils`.

This module tries to import ``secure_filename`` from an installed
``werkzeug`` package.  If that fails (because the real package isn't
available), a lightweight stub implementation is used instead.
"""

from __future__ import annotations

import importlib.util
import os
import sys


def _load_real_secure_filename():
    """Attempt to load ``secure_filename`` from a real Werkzeug install."""
    current = os.path.abspath(__file__)
    for path in sys.path[1:]:
        spec = importlib.util.find_spec("werkzeug.utils", [path])
        if spec and os.path.abspath(spec.origin) != current:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore[call-arg]
            return module.secure_filename
    raise ImportError


try:
    secure_filename = _load_real_secure_filename()
except Exception:  # pragma: no cover - fallback when Werkzeug is missing
    from werkzeug_stub.utils import secure_filename

