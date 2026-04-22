# AI Codebase Debugging & Intelligence Assistant Backend

FastAPI backend for ingesting codebases, embedding code chunks, retrieving relevant context, and producing debugging answers.

## Prerequisites

- Python 3.11+
- Git, for GitHub repository ingestion
- Ollama running locally
- Ollama models:

```bash
ollama pull nomic-embed-text
ollama pull codellama
ollama pull llama3
```

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will run at `http://localhost:8000`.

## Core Endpoints

- `GET /health`
- `POST /api/upload/zip` with form field `file`
- `POST /api/upload/github` with `repo_url` and optional `branch`
- `GET /api/upload/projects`
- `GET /api/upload/projects/{project_id}`
- `POST /api/query` with `project_id`, `question`, and optional `top_k`
- `POST /api/debug` with `project_id`, `error_message`, optional `stack_trace`, and optional `top_k`

## Notes

This backend does not execute uploaded code and does not edit user files. Debug responses return suggested patches as text only.
