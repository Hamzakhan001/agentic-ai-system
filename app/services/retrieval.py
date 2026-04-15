from __future__ import annotations

from collections import Counter

from app.core.models import InputDocument


class SimpleRetrievalService:
    """Keyword-overlap retriever for Phase 1.

    This keeps the MVP runnable before we add vector search.
    """

    def search(self, question: str, documents: list[InputDocument], top_k: int) -> list[InputDocument]:
        query_terms = [token.lower() for token in question.split() if token.strip()]
        if not query_terms:
            return documents[:top_k]

        query_counts = Counter(query_terms)
        scored: list[tuple[InputDocument, int]] = []
        for document in documents:
            doc_terms = document.text.lower().split()
            score = sum(query_counts[t] for t in doc_terms if t in query_counts)
            scored.append((document, score))

        ranked = sorted(scored, key=lambda item: item[1], reverse=True)
        return [doc for doc, score in ranked[:top_k] if score > 0] or documents[:top_k]
