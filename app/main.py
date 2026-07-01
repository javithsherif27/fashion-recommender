from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app import config
from app.llm import get_interpreter
from app.models import RecommendRequest, RecommendResponse
from app.search import ProductIndex

app = FastAPI(
    title="Semantic Fashion Recommendation Microservice",
    version="0.1.0",
    description="Take-home assignment service for semantic product recommendations.",
)

INDEX_PATH = config.INDEX_DIR
INDEX_CACHE: ProductIndex | None = None


def get_index() -> ProductIndex:
    global INDEX_CACHE
    if INDEX_CACHE is None:
        INDEX_CACHE = ProductIndex.load(INDEX_PATH)
    return INDEX_CACHE


@app.get("/")
def demo_page() -> FileResponse:
    page = Path(__file__).parent / "static" / "index.html"
    return FileResponse(page)


@app.get("/health")
def health() -> dict[str, object]:
    index_ready = (INDEX_PATH / "manifest.json").exists()
    payload: dict[str, object] = {
        "status": "ok",
        "index_ready": index_ready,
        "index_dir": str(INDEX_PATH),
        "llm_configured": bool(config.OPENAI_API_KEY),
    }
    if index_ready:
        try:
            index = get_index()
            payload.update(
                {
                    "product_count": len(index.products),
                    "embedding_backend": index.embedder.backend,
                    "embedding_model": index.embedder.model_name,
                }
            )
        except Exception as exc:
            payload["index_error"] = str(exc)
    return payload


@app.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest) -> dict[str, object]:
    try:
        index = get_index()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    interpreter = get_interpreter()
    return index.recommend(
        request.query,
        top_k=request.top_k,
        filters=request.filters,
        interpreter=interpreter,
    )

