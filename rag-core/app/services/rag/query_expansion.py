"""
Lightweight portfolio query expansion for embedding/retrieval only.

The original user question is still passed to the LLM. This only improves
semantic search when users say "you/your/this person" without naming Martín.
"""

from __future__ import annotations

import re

from app.core.collection import COLLECTION_PORTFOLIO, get_collection

_PORTFOLIO_SUBJECT = (
    "Martín Lavín Carvajal (Martin Lavin) education Nestlé internship "
    "skills projects Document Knowledge Agent Cloud Operations Lab "
    "ECG AI Serverless Skill Tracker"
)

_DEICTIC = re.compile(
    r"\b("
    r"you|your|yourself|yours|"
    r"this person|this guy|this candidate|"
    r"him|his|he\b"
    r")\b",
    re.IGNORECASE,
)


def expand_query_for_embedding(question: str) -> str:
    """
    Expand deictic portfolio questions before embedding.

    Accent stripping is intentionally not applied: OpenAI embeddings already
    handle Nestlé/Nestle and Martín/Martin well enough for this corpus.
    """
    text = (question or "").strip()
    if not text:
        return text

    if get_collection() != COLLECTION_PORTFOLIO:
        return text

    if _DEICTIC.search(text):
        return f"{text}\n\nSubject: {_PORTFOLIO_SUBJECT}."

    return text
