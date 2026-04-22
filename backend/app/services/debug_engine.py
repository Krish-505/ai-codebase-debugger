from __future__ import annotations

import re

from app.models.schema import DebugResponse, RetrievedChunk
from app.services.llm import OllamaLLM
from app.services.retriever import Retriever


class DebugEngine:
    def __init__(self, retriever: Retriever | None = None, llm: OllamaLLM | None = None):
        self.retriever = retriever or Retriever()
        self.llm = llm or OllamaLLM()

    def analyze(
        self,
        project_id: str,
        error_message: str,
        stack_trace: str | None,
        top_k: int,
    ) -> DebugResponse:
        file_hints = self._extract_file_hints(stack_trace or "")
        retrieval_query = self._build_retrieval_query(error_message, stack_trace, file_hints)
        chunks = self.retriever.retrieve_for_debug(project_id, retrieval_query, file_hints, top_k)
        prompt = self._build_prompt(error_message, stack_trace, chunks)
        raw_answer = self.llm.generate(prompt, model="llama3", temperature=0.05)
        return self._parse_response(raw_answer, chunks)

    def _build_retrieval_query(self, error_message: str, stack_trace: str | None, file_hints: list[str]) -> str:
        stack = stack_trace or ""
        return f"{error_message}\n{' '.join(file_hints)}\n{stack[:4000]}"

    def _extract_file_hints(self, stack_trace: str) -> list[str]:
        matches = re.findall(r"[\w./\\-]+\.(?:py|js|jsx|ts|tsx|java|go|rs|rb|php)", stack_trace)
        seen: set[str] = set()
        hints: list[str] = []
        for match in matches:
            normalized = match.replace("\\", "/").lstrip("./")
            if normalized not in seen:
                hints.append(normalized)
                seen.add(normalized)
        return hints

    def _build_prompt(self, error_message: str, stack_trace: str | None, chunks: list[RetrievedChunk]) -> str:
        context = "\n\n".join(self._format_chunk(chunk) for chunk in chunks)
        stack = stack_trace or "No stack trace provided."
        return f"""You are a senior debugging assistant for a codebase search system.
Analyze the error using only the supplied code context. Do not invent files or APIs.
Return the response with these exact section headers:

ROOT_CAUSE:
EXPLANATION:
FIX_SUGGESTION:
PATCH:

The PATCH section must be a unified diff. If there is not enough evidence for a safe patch,
return a minimal illustrative diff and clearly mark assumptions in FIX_SUGGESTION.

ERROR MESSAGE:
{error_message}

STACK TRACE:
{stack}

RELEVANT CODE CONTEXT:
{context}
"""

    def _format_chunk(self, chunk: RetrievedChunk) -> str:
        symbol = f"::{chunk.function_name}" if chunk.function_name else ""
        return (
            f"FILE: {chunk.file_path}{symbol} lines {chunk.start_line}-{chunk.end_line}\n"
            f"LANGUAGE: {chunk.language}\n"
            f"```{chunk.language}\n{chunk.content}\n```"
        )

    def _parse_response(self, raw_answer: str, chunks: list[RetrievedChunk]) -> DebugResponse:
        sections = {
            "root_cause": self._section(raw_answer, "ROOT_CAUSE"),
            "explanation": self._section(raw_answer, "EXPLANATION"),
            "fix_suggestion": self._section(raw_answer, "FIX_SUGGESTION"),
            "patch": self._section(raw_answer, "PATCH"),
        }
        if not any(sections.values()):
            sections["explanation"] = raw_answer
        return DebugResponse(
            root_cause=sections["root_cause"] or "Could not isolate a root cause from the retrieved context.",
            explanation=sections["explanation"] or raw_answer,
            fix_suggestion=sections["fix_suggestion"] or "Review the cited source chunks and provide more stack trace detail.",
            patch=sections["patch"] or "",
            sources=chunks,
        )

    def _section(self, text: str, name: str) -> str:
        pattern = re.compile(
            rf"{name}:\s*(.*?)(?=\n(?:ROOT_CAUSE|EXPLANATION|FIX_SUGGESTION|PATCH):|\Z)",
            re.DOTALL,
        )
        match = pattern.search(text)
        return match.group(1).strip() if match else ""
