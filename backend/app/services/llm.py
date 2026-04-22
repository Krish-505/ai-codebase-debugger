from __future__ import annotations

import os

import requests


class LLMError(RuntimeError):
    pass


class OllamaLLM:
    def __init__(self, base_url: str | None = None, timeout: int = 180):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/")
        self.timeout = timeout

    def generate(self, prompt: str, model: str = "llama3", temperature: float = 0.1) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature},
            },
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise LLMError(f"Ollama generation request failed: {response.text}")
        payload = response.json()
        answer = payload.get("response")
        if not isinstance(answer, str):
            raise LLMError("Ollama did not return a text response.")
        return answer.strip()
