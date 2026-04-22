from __future__ import annotations

import os
from typing import Any

from app.models.schema import CodeChunk, RetrievedChunk


class VectorStoreError(RuntimeError):
    pass


class ChromaVectorStore:
    def __init__(self, persist_directory: str | None = None):
        try:
            import chromadb
        except ImportError as exc:
            raise VectorStoreError("chromadb is not installed. Install backend requirements first.") from exc

        directory = persist_directory or os.getenv("CHROMA_PATH") or "storage/chroma"
        self.client = chromadb.PersistentClient(path=directory)

    def upsert_chunks(self, project_id: str, chunks: list[CodeChunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        collection = self._collection(project_id)
        collection.upsert(
            ids=[chunk.id for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.content for chunk in chunks],
            metadatas=[self._metadata(chunk) for chunk in chunks],
        )

    def query(self, project_id: str, embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        collection = self._collection(project_id)
        result = collection.query(query_embeddings=[embedding], n_results=top_k)
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        chunks: list[RetrievedChunk] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            chunks.append(self._retrieved_chunk(document, metadata, float(distance)))
        return chunks

    def get_by_file_hints(self, project_id: str, file_hints: list[str], limit: int = 6) -> list[RetrievedChunk]:
        if not file_hints:
            return []

        collection = self._collection(project_id)
        result = collection.get(include=["documents", "metadatas"])
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])
        normalized_hints = [self._normalize_path(hint) for hint in file_hints]

        matches: list[RetrievedChunk] = []
        for document, metadata in zip(documents, metadatas):
            file_path = self._normalize_path(str(metadata.get("file_path", "")))
            if any(file_path.endswith(hint) or hint.endswith(file_path) for hint in normalized_hints):
                matches.append(self._retrieved_chunk(document, metadata, None))
            if len(matches) >= limit:
                break
        return matches

    def _collection(self, project_id: str) -> Any:
        return self.client.get_or_create_collection(name=f"project_{project_id}")

    def _metadata(self, chunk: CodeChunk) -> dict[str, str | int | float | bool]:
        metadata: dict[str, str | int | float | bool] = {
            "project_id": chunk.project_id,
            "file_path": chunk.file_path,
            "language": chunk.language,
            "function_name": chunk.function_name or "",
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
        }
        for key, value in chunk.metadata.items():
            if isinstance(value, str | int | float | bool):
                metadata[key] = value
            elif value is not None:
                metadata[key] = str(value)
        return metadata

    def _retrieved_chunk(self, document: str, metadata: dict[str, Any], score: float | None) -> RetrievedChunk:
        return RetrievedChunk(
            file_path=str(metadata.get("file_path", "")),
            language=str(metadata.get("language", "text")),
            function_name=metadata.get("function_name") or None,
            content=document,
            start_line=int(metadata.get("start_line", 1)),
            end_line=int(metadata.get("end_line", 1)),
            score=score,
        )

    def _normalize_path(self, path: str) -> str:
        return path.replace("\\", "/").lstrip("./").lower()
