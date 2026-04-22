from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schema import DebugRequest, DebugResponse
from app.services.debug_engine import DebugEngine
from app.services.embeddings import EmbeddingError
from app.services.llm import LLMError
from app.services.vector_store import VectorStoreError


router = APIRouter()


@router.post("", response_model=DebugResponse)
def debug_codebase(request: DebugRequest) -> DebugResponse:
    try:
        return DebugEngine().analyze(
            project_id=request.project_id,
            error_message=request.error_message,
            stack_trace=request.stack_trace,
            top_k=request.top_k,
        )
    except (EmbeddingError, VectorStoreError, LLMError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
