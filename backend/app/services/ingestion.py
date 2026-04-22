from __future__ import annotations

from pathlib import Path

from app.models.schema import IngestedFile, IngestionResponse, UploadSource
from app.services.chunker import CodeChunker
from app.services.embeddings import OllamaEmbeddings
from app.services.vector_store import ChromaVectorStore
from app.utils.file_loader import iter_code_files, language_from_path, read_text_file


class IngestionService:
    def __init__(
        self,
        chunker: CodeChunker | None = None,
        embeddings: OllamaEmbeddings | None = None,
        vector_store: ChromaVectorStore | None = None,
    ):
        self.chunker = chunker or CodeChunker()
        self.embeddings = embeddings or OllamaEmbeddings()
        self.vector_store = vector_store or ChromaVectorStore()

    def ingest_path(self, project_id: str, root: Path, source: UploadSource) -> IngestionResponse:
        code_files = iter_code_files(root)
        total_files = len([path for path in root.rglob("*") if path.is_file()])
        indexed_files: list[IngestedFile] = []
        all_chunks = []

        for path in code_files:
            relative_path = path.relative_to(root).as_posix()
            content = read_text_file(path)
            chunks = self.chunker.chunk_file(project_id, path, relative_path, content)
            if not chunks:
                continue
            all_chunks.extend(chunks)
            indexed_files.append(
                IngestedFile(
                    path=relative_path,
                    language=language_from_path(path),
                    size_bytes=path.stat().st_size,
                    chunks=len(chunks),
                )
            )

        if all_chunks:
            embeddings = self.embeddings.embed_many([chunk.content for chunk in all_chunks])
            self.vector_store.upsert_chunks(project_id, all_chunks, embeddings)

        return IngestionResponse(
            project_id=project_id,
            source=source,
            files_indexed=len(indexed_files),
            chunks_indexed=len(all_chunks),
            ignored_files=max(0, total_files - len(code_files)),
            files=indexed_files,
        )
