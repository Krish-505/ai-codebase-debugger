from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class UploadSource(str, Enum):
    zip = "zip"
    github = "github"


class CodeChunk(BaseModel):
    id: str
    project_id: str
    file_path: str
    language: str
    function_name: str | None = None
    content: str
    start_line: int = 1
    end_line: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestedFile(BaseModel):
    path: str
    language: str
    size_bytes: int
    chunks: int


class IngestionResponse(BaseModel):
    project_id: str
    source: UploadSource
    files_indexed: int
    chunks_indexed: int
    ignored_files: int
    files: list[IngestedFile]


class ProjectSummary(BaseModel):
    project_id: str
    source: UploadSource
    source_name: str
    created_at: str
    files_indexed: int
    chunks_indexed: int


class ProjectDetail(ProjectSummary):
    ignored_files: int
    files: list[IngestedFile]


class GitHubIngestRequest(BaseModel):
    repo_url: HttpUrl
    branch: str | None = None


class QueryRequest(BaseModel):
    project_id: str
    question: str = Field(min_length=1)
    top_k: int = Field(default=6, ge=1, le=20)


class RetrievedChunk(BaseModel):
    file_path: str
    language: str
    function_name: str | None = None
    content: str
    start_line: int
    end_line: int
    score: float | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[RetrievedChunk]


class DebugRequest(BaseModel):
    project_id: str
    error_message: str = Field(min_length=1)
    stack_trace: str | None = None
    top_k: int = Field(default=8, ge=1, le=20)


class DebugResponse(BaseModel):
    root_cause: str
    explanation: str
    fix_suggestion: str
    patch: str
    sources: list[RetrievedChunk]
