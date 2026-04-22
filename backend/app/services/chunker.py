from __future__ import annotations

import hashlib
from pathlib import Path

from app.models.schema import CodeChunk
from app.services.parser import CodeParser, Symbol
from app.utils.file_loader import language_from_path


class CodeChunker:
    def __init__(
        self,
        parser: CodeParser | None = None,
        max_lines: int = 80,
        overlap: int = 12,
        max_chars: int = 4000,
        char_overlap: int = 300,
    ):
        self.parser = parser or CodeParser()
        self.max_lines = max_lines
        self.overlap = overlap
        self.max_chars = max_chars
        self.char_overlap = char_overlap

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
                    for chunk_content, chunk_start, chunk_end in self._split_oversized_content(
                        content,
                        window_start,
                        window_end,
                    ):
                        chunks.append(
                            self._build_chunk(
                                project_id,
                                relative_path,
                                language,
                                chunk_content,
                                chunk_start,
                                chunk_end,
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
                for chunk_content, chunk_start, chunk_end in self._split_oversized_content(
                    content,
                    start_index + 1,
                    end_index,
                ):
                    chunks.append(
                        self._build_chunk(
                            project_id,
                            relative_path,
                            language,
                            chunk_content,
                            chunk_start,
                            chunk_end,
                            None,
                        )
                    )
            if end_index >= len(lines):
                break
        return chunks

    def _split_oversized_content(self, content: str, start_line: int, end_line: int) -> list[tuple[str, int, int]]:
        if len(content) <= self.max_chars:
            return [(content, start_line, end_line)]

        lines = content.splitlines()
        if len(lines) <= 1:
            return [(part, start_line, end_line) for part in self._split_long_text(content)]

        chunks: list[tuple[str, int, int]] = []
        current_lines: list[str] = []
        current_start = start_line

        for offset, line in enumerate(lines):
            line_number = start_line + offset
            next_content = "\n".join([*current_lines, line]).strip()
            if current_lines and len(next_content) > self.max_chars:
                chunk_content = "\n".join(current_lines).strip()
                chunks.append((chunk_content, current_start, line_number - 1))
                current_lines = [line]
                current_start = line_number
                continue

            if len(line) > self.max_chars:
                if current_lines:
                    chunk_content = "\n".join(current_lines).strip()
                    chunks.append((chunk_content, current_start, line_number - 1))
                    current_lines = []
                chunks.extend((part, line_number, line_number) for part in self._split_long_text(line))
                current_start = line_number + 1
                continue

            current_lines.append(line)

        if current_lines:
            chunk_content = "\n".join(current_lines).strip()
            chunks.append((chunk_content, current_start, start_line + len(lines) - 1))

        return [(chunk, chunk_start, chunk_end) for chunk, chunk_start, chunk_end in chunks if chunk]

    def _split_long_text(self, text: str) -> list[str]:
        chunks: list[str] = []
        step = max(1, self.max_chars - self.char_overlap)
        for start in range(0, len(text), step):
            chunk = text[start : start + self.max_chars].strip()
            if chunk:
                chunks.append(chunk)
            if start + self.max_chars >= len(text):
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
