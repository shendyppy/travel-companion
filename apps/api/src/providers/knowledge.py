"""
Knowledge base retrieval.

A ChromaDB collection of travel guide passages, queried with embeddings that run
locally inside the container.

Why local embeddings: generation is bring-your-own-key, so retrieval must not
also need an API key. If it did, "bring your own key" would be a lie -- the
server would still pay for an embedding call on every query. Running the ONNX
model in-process means the user's key touches exactly one thing, generation, and
that is easy to explain and easy to audit.

The index is read-only at runtime and baked into the Docker image at build time
(see scripts/build_index.py). Cloud Run has an ephemeral filesystem and scales
to zero, so a writable on-disk store would not survive anyway; the corpus is
curated travel content that changes rarely, which makes a baked index the right
shape rather than a compromise.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Optional

from src.config import DATA_DIR

logger = logging.getLogger(__name__)

CHROMA_DIR = DATA_DIR / "chroma"
COLLECTION = "travel_knowledge"

# all-MiniLM-L6-v2 via ONNX: ChromaDB's default, ~80MB, no API key, no network.
# Good enough for retrieving travel guide passages, and it keeps the image small
# enough to stay comfortable on Cloud Run.
EMBEDDING_MODEL = "all-MiniLM-L6-v2 (ONNX, local)"


@dataclass
class Passage:
    text: str
    title: str
    city: Optional[str]
    section: Optional[str]
    source: str
    url: Optional[str]
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "title": self.title,
            "city": self.city,
            "section": self.section,
            "source": self.source,
            "url": self.url,
            "relevance": round(self.score, 3),
        }


class KnowledgeBaseUnavailable(RuntimeError):
    """Raised when the index has not been built."""


@lru_cache(maxsize=1)
def _collection():
    """
    Open the collection. Cached because loading the embedding model costs about a
    second, and it is the same model for every request.
    """
    if not CHROMA_DIR.exists():
        raise KnowledgeBaseUnavailable(
            f"No knowledge index at {CHROMA_DIR}. Run: python -m scripts.build_index"
        )

    import chromadb

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        return client.get_collection(COLLECTION)
    except Exception as exc:
        raise KnowledgeBaseUnavailable(
            f"Collection '{COLLECTION}' missing. Run: python -m scripts.build_index"
        ) from exc


def is_available() -> bool:
    try:
        _collection()
        return True
    except Exception:
        return False


def stats() -> dict[str, Any]:
    try:
        collection = _collection()
        return {
            "available": True,
            "passages": collection.count(),
            "embedding": EMBEDDING_MODEL,
            "path": str(CHROMA_DIR),
        }
    except KnowledgeBaseUnavailable as exc:
        return {"available": False, "reason": str(exc)}


def search(
    query: str,
    *,
    city: Optional[str] = None,
    section: Optional[str] = None,
    limit: int = 5,
) -> list[Passage]:
    """
    Retrieve passages relevant to a query.

    `city` and `section` become metadata filters rather than being folded into
    the query text. Semantic similarity is poor at hard constraints -- asking for
    "Bali" in the query still surfaces Lombok passages, because they are
    genuinely similar. A filter is exact.
    """
    collection = _collection()

    conditions = []
    if city:
        conditions.append({"city": {"$eq": city.strip().lower()}})
    if section:
        conditions.append({"section": {"$eq": section.strip().lower()}})

    where: Optional[dict[str, Any]] = None
    if len(conditions) == 1:
        where = conditions[0]
    elif conditions:
        where = {"$and": conditions}

    result = collection.query(
        query_texts=[query],
        n_results=max(1, min(limit, 20)),
        where=where,
    )

    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    passages: list[Passage] = []
    for text, meta, distance in zip(documents, metadatas, distances):
        meta = meta or {}
        passages.append(
            Passage(
                text=text,
                title=meta.get("title") or "",
                city=meta.get("city"),
                section=meta.get("section"),
                source=meta.get("source") or "unknown",
                url=meta.get("url"),
                # Chroma returns squared L2 distance; smaller is closer. Mapped to
                # a 0-1 relevance purely so the number reads sensibly downstream.
                score=1.0 / (1.0 + float(distance)),
            )
        )
    return passages
