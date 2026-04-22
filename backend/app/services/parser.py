from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.utils.file_loader import language_from_path


@dataclass(frozen=True)
class Symbol:
    name: str
    start_line: int
    end_line: int


class CodeParser:
    """Finds coarse function/class symbols with Tree-sitter and a regex fallback.

    The fallback is intentionally conservative. It gives the retrieval layer useful
    metadata without blocking ingestion for languages that do not have a grammar installed.
    """

    def parse_symbols(self, path: Path, content: str) -> list[Symbol]:
        language = language_from_path(path)
        tree_sitter_symbols = self._tree_sitter_symbols(language, content)
        if tree_sitter_symbols:
            return tree_sitter_symbols

        lines = content.splitlines()
        candidates = self._regex_symbols(language, lines)
        if not candidates:
            return []
        return self._estimate_symbol_ranges(candidates, len(lines))

    def _tree_sitter_symbols(self, language: str, content: str) -> list[Symbol]:
        try:
            from tree_sitter_language_pack import get_parser

            parser = get_parser(language)
        except Exception:
            return []

        try:
            tree = parser.parse(content.encode("utf-8"))
        except Exception:
            return []

        symbols: list[Symbol] = []
        symbol_node_types = {
            "class_declaration",
            "class_definition",
            "enum_declaration",
            "function_declaration",
            "function_definition",
            "function_item",
            "interface_declaration",
            "method_declaration",
            "method_definition",
            "trait_item",
            "type_alias_declaration",
        }

        def visit(node: object) -> None:
            node_type = getattr(node, "type", "")
            if node_type in symbol_node_types:
                name = self._node_name(node, content)
                if name:
                    start_line = getattr(node, "start_point", (0, 0))[0] + 1
                    end_line = getattr(node, "end_point", (0, 0))[0] + 1
                    symbols.append(Symbol(name=name, start_line=start_line, end_line=end_line))
            for child in getattr(node, "children", []):
                visit(child)

        visit(tree.root_node)
        return symbols

    def _node_name(self, node: object, content: str) -> str | None:
        child_by_field_name = getattr(node, "child_by_field_name", None)
        name_node = child_by_field_name("name") if callable(child_by_field_name) else None
        if name_node is None:
            for child in getattr(node, "children", []):
                if getattr(child, "type", "") == "identifier":
                    name_node = child
                    break
        if name_node is None:
            return None
        start = getattr(name_node, "start_byte", None)
        end = getattr(name_node, "end_byte", None)
        if start is None or end is None:
            return None
        return content.encode("utf-8")[start:end].decode("utf-8", errors="ignore")

    def _regex_symbols(self, language: str, lines: list[str]) -> list[tuple[str, int]]:
        patterns = {
            "python": [
                re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_][\w]*)\s*\("),
                re.compile(r"^\s*class\s+([A-Za-z_][\w]*)\s*[\(:]"),
            ],
            "javascript": [
                re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("),
                re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\("),
                re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z_$][\w$]*)\b"),
            ],
            "typescript": [
                re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("),
                re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*[:=]"),
                re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z_$][\w$]*)\b"),
                re.compile(r"^\s*(?:export\s+)?interface\s+([A-Za-z_$][\w$]*)\b"),
                re.compile(r"^\s*(?:export\s+)?type\s+([A-Za-z_$][\w$]*)\b"),
            ],
            "java": [
                re.compile(r"^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:class|interface|enum)\s+([A-Za-z_][\w]*)\b"),
                re.compile(r"^\s*(?:public|private|protected)?\s*(?:static\s+)?[\w<>\[\], ?]+\s+([A-Za-z_][\w]*)\s*\("),
            ],
            "go": [
                re.compile(r"^\s*func\s+(?:\([^)]+\)\s*)?([A-Za-z_][\w]*)\s*\("),
                re.compile(r"^\s*type\s+([A-Za-z_][\w]*)\s+(?:struct|interface)\b"),
            ],
            "rust": [
                re.compile(r"^\s*(?:pub\s+)?fn\s+([A-Za-z_][\w]*)\s*\("),
                re.compile(r"^\s*(?:pub\s+)?(?:struct|enum|trait)\s+([A-Za-z_][\w]*)\b"),
            ],
        }
        selected = patterns.get(language, [])
        matches: list[tuple[str, int]] = []
        for index, line in enumerate(lines, start=1):
            for pattern in selected:
                match = pattern.search(line)
                if match:
                    matches.append((match.group(1), index))
                    break
        return matches

    def _estimate_symbol_ranges(self, candidates: list[tuple[str, int]], total_lines: int) -> list[Symbol]:
        symbols: list[Symbol] = []
        for index, (name, start_line) in enumerate(candidates):
            next_start = candidates[index + 1][1] if index + 1 < len(candidates) else total_lines + 1
            symbols.append(Symbol(name=name, start_line=start_line, end_line=max(start_line, next_start - 1)))
        return symbols
