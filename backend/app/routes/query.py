from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schema import QueryRequest, QueryResponse
from app.services.embeddings import EmbeddingError
from app.services.llm import LLMError
from app.services.query_engine import QueryEngine
from app.services.vector_store import VectorStoreError


router = APIRouter()


@router.post("", response_model=QueryResponse)
def query_codebase(request: QueryRequest) -> QueryResponse:
    try:
        return QueryEngine().answer(request.project_id, request.question, request.top_k)
    except (EmbeddingError, VectorStoreError, LLMError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
