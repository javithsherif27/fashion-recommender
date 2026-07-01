from __future__ import annotations

from pydantic import BaseModel, Field


class ProductFilters(BaseModel):
    max_price: float | None = Field(default=None, ge=0)
    min_rating: float | None = Field(default=None, ge=0, le=5)
    require_price: bool = False


class RecommendRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    filters: ProductFilters = Field(default_factory=ProductFilters)


class Recommendation(BaseModel):
    parent_asin: str
    title: str
    store: str | None
    price: float | None
    average_rating: float | None
    rating_number: int | None
    score: float
    why: str


class RecommendResponse(BaseModel):
    query: str
    interpreted_query: str
    llm_used: bool
    llm_provider: str
    embedding_backend: str
    recommendations: list[Recommendation]
    latency_ms: int
    message: str | None = None
