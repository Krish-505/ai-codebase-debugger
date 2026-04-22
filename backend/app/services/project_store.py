from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.models.schema import IngestionResponse, ProjectDetail, ProjectSummary, UploadSource
from app.utils.file_loader import STORAGE_ROOT


class ProjectStore:
    def __init__(self, metadata_path: Path | None = None):
        self.metadata_path = metadata_path or STORAGE_ROOT / "projects.json"
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, ingestion: IngestionResponse, source_name: str) -> ProjectDetail:
        projects = self._read()
        detail = ProjectDetail(
            project_id=ingestion.project_id,
            source=ingestion.source,
            source_name=source_name,
            created_at=datetime.now(timezone.utc).isoformat(),
            files_indexed=ingestion.files_indexed,
            chunks_indexed=ingestion.chunks_indexed,
            ignored_files=ingestion.ignored_files,
            files=ingestion.files,
        )
        projects[ingestion.project_id] = detail.model_dump(mode="json")
        self._write(projects)
        return detail

    def list(self) -> list[ProjectSummary]:
        projects = self._read()
        summaries = [
            ProjectSummary(
                project_id=project["project_id"],
                source=UploadSource(project["source"]),
                source_name=project["source_name"],
                created_at=project["created_at"],
                files_indexed=project["files_indexed"],
                chunks_indexed=project["chunks_indexed"],
            )
            for project in projects.values()
        ]
        return sorted(summaries, key=lambda project: project.created_at, reverse=True)

    def get(self, project_id: str) -> ProjectDetail | None:
        project = self._read().get(project_id)
        return ProjectDetail.model_validate(project) if project else None

    def _read(self) -> dict[str, dict]:
        if not self.metadata_path.exists():
            return {}
        with self.metadata_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _write(self, projects: dict[str, dict]) -> None:
        with self.metadata_path.open("w", encoding="utf-8") as file:
            json.dump(projects, file, indent=2)
