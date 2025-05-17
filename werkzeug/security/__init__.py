"""Compatibility wrapper for :mod:`werkzeug.security`.

This module tries to import ``generate_password_hash`` and
``check_password_hash`` from an installed ``werkzeug`` package. If the real
package is not available, lightweight stub implementations are used instead.
"""

from __future__ import annotations

import importlib.util
import os
import sys


def _load_real_security():
    """Attempt to load password utilities from a real Werkzeug install."""
    current = os.path.abspath(__file__)
    for path in sys.path[1:]:
        spec = importlib.util.find_spec("werkzeug.security", [path])
        if spec and os.path.abspath(spec.origin) != current:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore[call-arg]
            return module.generate_password_hash, module.check_password_hash
    raise ImportError


try:
    generate_password_hash, check_password_hash = _load_real_security()
except Exception:  # pragma: no cover - fallback when Werkzeug is missing
    from werkzeug_stub.security import (
        generate_password_hash,
        check_password_hash,
    )
