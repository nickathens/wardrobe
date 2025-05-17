"""Minimal password hashing utilities used when Werkzeug is missing."""

from __future__ import annotations
import hashlib


def generate_password_hash(password: str) -> str:
    """Return a deterministic hash for ``password``."""
    return "stub$" + hashlib.sha256(password.encode()).hexdigest()


def check_password_hash(pwhash: str, password: str) -> bool:
    """Return True if ``password`` matches ``pwhash``."""
    return pwhash == generate_password_hash(password)
