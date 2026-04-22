from __future__ import annotations

import hashlib
from pathlib import Path

from app.models.schema import CodeChunk
from app.services.parser import CodeParser, Symbol
from app.utils.file_loader import language_from_path


class CodeChunker:
    def __init__(self, parser: CodeParser | None = None, max_lines: int = 80, overlap: int = 12):
        self.parser = parser or CodeParser()
        self.max_lines = max_lines
        self.overlap = overlap

    def chunk_file(self, project_id: str, path: Path, relative_path: str, content: str) -> list[CodeChunk]:
        language = language_from_path(path)
        lines = content.splitlines()
        if not lines:
            return []

        symbols = self.parser.parse_symbols(path, content)
        chunks = self._chunk_by_symbols(project_id, relative_path, language, lines, symbols)
        if chunks:
            return chunks
        return self._sliding_window_chunks(project_id, relative_path, language, lines)

    def _chunk_by_symbols(
        self,
        project_id: str,
        relative_path: str,
        language: str,
        lines: list[str],
        symbols: list[Symbol],
    ) -> list[CodeChunk]:
        chunks: list[CodeChunk] = []
        for symbol in symbols:
            start = max(symbol.start_line, 1)
            end = min(symbol.end_line, len(lines))
            for window_start in range(start, end + 1, max(1, self.max_lines - self.overlap)):
                window_end = min(end, window_start + self.max_lines - 1)
                content = "\n".join(lines[window_start - 1 : window_end]).strip()
                if content:
                    chunks.append(
                        self._build_chunk(
                            project_id,
                            relative_path,
                            language,
                            content,
                            window_start,
                            window_end,
                            symbol.name,
                        )
                    )
                if window_end >= end:
                    break
        return chunks

    def _sliding_window_chunks(
        self,
        project_id: str,
        relative_path: str,
        language: str,
        lines: list[str],
    ) -> list[CodeChunk]:
        chunks: list[CodeChunk] = []
        step = max(1, self.max_lines - self.overlap)
        for start_index in range(0, len(lines), step):
            end_index = min(len(lines), start_index + self.max_lines)
            content = "\n".join(lines[start_index:end_index]).strip()
            if content:
                chunks.append(
                    self._build_chunk(
                        project_id,
                        relative_path,
                        language,
                        content,
                        start_index + 1,
                        end_index,
                        None,
                    )
                )
            if end_index >= len(lines):
                break
        return chunks

    def _build_chunk(
        self,
        project_id: str,
        relative_path: str,
        language: str,
        content: str,
        start_line: int,
        end_line: int,
        function_name: str | None,
    ) -> CodeChunk:
        digest = hashlib.sha256(f"{relative_path}:{start_line}:{end_line}:{content}".encode()).hexdigest()[:16]
        return CodeChunk(
            id=f"{project_id}:{digest}",
            project_id=project_id,
            file_path=relative_path,
            language=language,
            function_name=function_name,
            content=content,
            start_line=start_line,
            end_line=end_line,
            metadata={"chunk_type": "symbol" if function_name else "window"},
        )
