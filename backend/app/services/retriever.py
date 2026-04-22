from __future__ import annotations

from app.models.schema import RetrievedChunk
from app.services.embeddings import OllamaEmbeddings
from app.services.vector_store import ChromaVectorStore


class Retriever:
    def __init__(self, embeddings: OllamaEmbeddings | None = None, vector_store: ChromaVectorStore | None = None):
        self.embeddings = embeddings or OllamaEmbeddings()
        self.vector_store = vector_store or ChromaVectorStore()

    def retrieve(self, project_id: str, query: str, top_k: int = 6) -> list[RetrievedChunk]:
        query_embedding = self.embeddings.embed(query)
        return self.vector_store.query(project_id, query_embedding, top_k)

    def retrieve_for_debug(
        self,
        project_id: str,
        query: str,
        file_hints: list[str],
        top_k: int = 8,
    ) -> list[RetrievedChunk]:
        hinted_chunks = self.vector_store.get_by_file_hints(project_id, file_hints, limit=max(1, top_k // 2))
        semantic_chunks = self.retrieve(project_id, query, top_k)

        combined: list[RetrievedChunk] = []
        seen: set[tuple[str, int, int]] = set()
        for chunk in [*hinted_chunks, *semantic_chunks]:
            key = (chunk.file_path, chunk.start_line, chunk.end_line)
            if key not in seen:
                combined.append(chunk)
                seen.add(key)
            if len(combined) >= top_k:
                break
        return combined
