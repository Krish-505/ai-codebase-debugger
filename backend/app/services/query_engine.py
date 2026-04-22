from __future__ import annotations

from app.models.schema import QueryResponse, RetrievedChunk
from app.services.llm import OllamaLLM
from app.services.retriever import Retriever


class QueryEngine:
    def __init__(self, retriever: Retriever | None = None, llm: OllamaLLM | None = None):
        self.retriever = retriever or Retriever()
        self.llm = llm or OllamaLLM()

    def answer(self, project_id: str, question: str, top_k: int) -> QueryResponse:
        chunks = self.retriever.retrieve(project_id, question, top_k)
        prompt = self._build_prompt(question, chunks)
        answer = self.llm.generate(prompt, model="llama3", temperature=0.1)
        return QueryResponse(answer=answer, sources=chunks)

    def _build_prompt(self, question: str, chunks: list[RetrievedChunk]) -> str:
        context = "\n\n".join(self._format_chunk(chunk) for chunk in chunks)
        return f"""You are an AI codebase intelligence assistant.
Answer the user's question using only the provided repository context.
If the answer is uncertain, say what evidence is missing.
Mention file paths and line numbers when useful.

USER QUESTION:
{question}

REPOSITORY CONTEXT:
{context}

ANSWER:"""

    def _format_chunk(self, chunk: RetrievedChunk) -> str:
        symbol = f"::{chunk.function_name}" if chunk.function_name else ""
        return (
            f"FILE: {chunk.file_path}{symbol} lines {chunk.start_line}-{chunk.end_line}\n"
            f"LANGUAGE: {chunk.language}\n"
            f"```{chunk.language}\n{chunk.content}\n```"
        )
