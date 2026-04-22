from __future__ import annotations

import os
import shutil
import subprocess
import uuid
import zipfile
from pathlib import Path
from urllib.parse import urlparse

from fastapi import UploadFile


RELEVANT_EXTENSIONS = {
    ".c",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".json",
    ".kt",
    ".md",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".sql",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
    ".yaml",
    ".yml",
}

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".idea",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".svn",
    ".venv",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "venv",
    "__pycache__",
}

MAX_FILE_BYTES = 512 * 1024

STORAGE_ROOT = Path(os.getenv("CODE_ASSISTANT_STORAGE", "storage")).resolve()
UPLOAD_ROOT = STORAGE_ROOT / "uploads"
REPO_ROOT = STORAGE_ROOT / "repos"


def ensure_storage() -> None:
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    REPO_ROOT.mkdir(parents=True, exist_ok=True)


def new_project_id() -> str:
    return uuid.uuid4().hex


async def save_upload_zip(file: UploadFile, project_id: str) -> Path:
    ensure_storage()
    archive_path = UPLOAD_ROOT / f"{project_id}.zip"
    with archive_path.open("wb") as destination:
        while chunk := await file.read(1024 * 1024):
            destination.write(chunk)
    return archive_path


def extract_zip_safely(archive_path: Path, project_id: str) -> Path:
    destination = REPO_ROOT / project_id
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if not str(target).startswith(str(destination)):
                raise ValueError(f"Unsafe ZIP entry rejected: {member.filename}")
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
    return destination


def clone_github_repo(repo_url: str, project_id: str, branch: str | None = None) -> Path:
    ensure_storage()
    parsed = urlparse(repo_url)
    if parsed.scheme not in {"https", "http"} or parsed.netloc.lower() != "github.com":
        raise ValueError("Only GitHub HTTPS repository URLs are supported.")

    destination = REPO_ROOT / project_id
    if destination.exists():
        shutil.rmtree(destination)

    command = ["git", "clone", "--depth", "1"]
    if branch:
        command.extend(["--branch", branch])
    command.extend([repo_url, str(destination)])
    subprocess.run(command, check=True, capture_output=True, text=True)
    return destination


def should_include_file(path: Path) -> bool:
    if any(part in IGNORED_DIRS for part in path.parts):
        return False
    if path.suffix.lower() not in RELEVANT_EXTENSIONS:
        return False
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return False
    except OSError:
        return False
    return True


def iter_code_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*") if path.is_file() and should_include_file(path)]


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def language_from_path(path: Path) -> str:
    suffix = path.suffix.lower()
    return {
        ".c": "c",
        ".cpp": "cpp",
        ".cs": "csharp",
        ".css": "css",
        ".go": "go",
        ".html": "html",
        ".java": "java",
        ".js": "javascript",
        ".jsx": "javascript",
        ".json": "json",
        ".kt": "kotlin",
        ".md": "markdown",
        ".php": "php",
        ".py": "python",
        ".rb": "ruby",
        ".rs": "rust",
        ".sql": "sql",
        ".swift": "swift",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".vue": "vue",
        ".yaml": "yaml",
        ".yml": "yaml",
    }.get(suffix, "text")
