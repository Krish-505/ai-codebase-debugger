from __future__ import annotations

import os

import requests


class EmbeddingError(RuntimeError):
    pass


class OllamaEmbeddings:
    def __init__(self, model: str = "nomic-embed-text", base_url: str | None = None, timeout: int = 60):
        self.model = model
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/")
        self.timeout = timeout

    def embed(self, text: str) -> list[float]:
        response = requests.post(
            f"{self.base_url}/api/embeddings",
            json={"model": self.model, "prompt": text},
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise EmbeddingError(f"Ollama embedding request failed: {response.text}")
        payload = response.json()
        embedding = payload.get("embedding")
        if not isinstance(embedding, list):
            raise EmbeddingError("Ollama did not return an embedding vector.")
        return embedding

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]
