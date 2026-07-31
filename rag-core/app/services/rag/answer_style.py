"""
Portfolio-only answer style helpers.

Keeps the demo RAG path untouched.
"""

from __future__ import annotations

import re

# Em dash and en dash (models sometimes emit either).
_DASH_CHARS = ("\u2014", "\u2013")

# "word — word" / "word—word" -> "word, word"
_SURROUNDED_DASH = re.compile(r"(\S)\s*[\u2014\u2013]\s*(\S)")


def strip_em_dashes(text: str) -> str:
    """Replace em/en dashes with commas for more natural prose."""
    if not text:
        return text

    cleaned = _SURROUNDED_DASH.sub(r"\1, \2", text)
    for dash in _DASH_CHARS:
        cleaned = cleaned.replace(dash, ",")
    # Tidy accidental double commas / spaces from edge cases.
    cleaned = re.sub(r",\s*,+", ",", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned
