"""
Request-scoped knowledge-base collection.

`default`  → demo RAG (existing Aurora/Chroma collection)
`portfolio` → Ask-me-anything portfolio corpus (isolated table/collection)

Selected via the `X-RAG-Collection` header (set by API Gateway / clients).
Omitting the header keeps full backward compatibility with the demo.
"""

from __future__ import annotations

from contextvars import ContextVar, Token

from app.core.config import settings

COLLECTION_DEFAULT = "default"
COLLECTION_PORTFOLIO = "portfolio"
ALLOWED_COLLECTIONS = frozenset({COLLECTION_DEFAULT, COLLECTION_PORTFOLIO})

_collection: ContextVar[str] = ContextVar(
    "rag_collection", default=COLLECTION_DEFAULT
)


def normalize_collection(value: str | None) -> str:
    if not value:
        return COLLECTION_DEFAULT
    normalized = value.strip().lower()
    if normalized not in ALLOWED_COLLECTIONS:
        return COLLECTION_DEFAULT
    return normalized


def get_collection() -> str:
    return _collection.get()


def set_collection(value: str | None) -> Token:
    return _collection.set(normalize_collection(value))


def reset_collection(token: Token) -> None:
    _collection.reset(token)


def resolve_aurora_table() -> str:
    collection = get_collection()
    if collection == COLLECTION_PORTFOLIO:
        return settings.AURORA_PORTFOLIO_TABLE_NAME
    return settings.AURORA_TABLE_NAME


def resolve_chroma_collection() -> str:
    collection = get_collection()
    if collection == COLLECTION_PORTFOLIO:
        return settings.CHROMA_PORTFOLIO_COLLECTION
    return settings.CHROMA_COLLECTION
