from __future__ import annotations

import subprocess

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schema import GitHubIngestRequest, IngestionResponse, ProjectDetail, ProjectSummary, UploadSource
from app.services.embeddings import EmbeddingError
from app.services.ingestion import IngestionService
from app.services.project_store import ProjectStore
from app.services.vector_store import VectorStoreError
from app.utils.file_loader import clone_github_repo, extract_zip_safely, new_project_id, save_upload_zip


router = APIRouter()


@router.get("/projects", response_model=list[ProjectSummary])
def list_projects() -> list[ProjectSummary]:
    return ProjectStore().list()


@router.get("/projects/{project_id}", response_model=ProjectDetail)
def get_project(project_id: str) -> ProjectDetail:
    project = ProjectStore().get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@router.post("/zip", response_model=IngestionResponse)
async def upload_zip(file: UploadFile = File(...)) -> IngestionResponse:
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Upload must be a .zip file.")

    project_id = new_project_id()
    try:
        archive_path = await save_upload_zip(file, project_id)
        root = extract_zip_safely(archive_path, project_id)
        response = IngestionService().ingest_path(project_id, root, UploadSource.zip)
        ProjectStore().save(response, file.filename)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (EmbeddingError, VectorStoreError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/github", response_model=IngestionResponse)
def upload_github(request: GitHubIngestRequest) -> IngestionResponse:
    project_id = new_project_id()
    try:
        root = clone_github_repo(str(request.repo_url), project_id, request.branch)
        response = IngestionService().ingest_path(project_id, root, UploadSource.github)
        ProjectStore().save(response, str(request.repo_url))
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or "Unable to clone GitHub repository."
        raise HTTPException(status_code=400, detail=detail) from exc
    except (EmbeddingError, VectorStoreError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
