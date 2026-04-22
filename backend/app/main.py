from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import debug, query, upload


app = FastAPI(
    title="AI Codebase Debugging & Intelligence Assistant",
    description="Ingest codebases, retrieve relevant code, and produce debugging guidance.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(query.router, prefix="/api/query", tags=["query"])
app.include_router(debug.router, prefix="/api/debug", tags=["debug"])


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
