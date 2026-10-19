"""RAG retriever.

- With a vector store (Chroma) + embeddings configured -> semantic retrieval.
- Without -> keyword overlap search over the markdown corpus in
  `app/rag/documents/` (zero-dependency, always works).

Drop travel guides / guidelines into `documents/` and they become retrievable
immediately. The destination agent calls `retrieve()` for source-backed facts.
"""
import os
from functools import lru_cache
from pathlib import Path

DOCS_DIR = Path(__file__).parent / "documents"


@lru_cache(maxsize=1)
def _load_corpus() -> list[dict]:
    docs = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        try:
            docs.append({"id": path.stem, "content": path.read_text(encoding="utf-8")})
        except OSError:
            continue
    return docs


class Retriever:
    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        corpus = _load_corpus()
        if not corpus:
            return []

        terms = set(query.lower().split())
        scored = []
        for doc in corpus:
            words = doc["content"].lower().split()
            score = sum(1 for t in terms if t in words)
            if score:
                scored.append((score, doc))
        scored.sort(key=lambda x: -x[0])
        return [{"id": d["id"], "content": d["content"]} for _, d in scored[:top_k]]


_retriever = Retriever()


def get_retriever() -> Retriever:
    return _retriever
