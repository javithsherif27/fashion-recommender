from __future__ import annotations

from fastapi.testclient import TestClient

from app.embedding import HashingEmbedder
from app.ingest import ProductRecord
from app.search import build_index


def test_health_and_recommend(monkeypatch, tmp_path) -> None:
    products = [
        ProductRecord(
            parent_asin="RUN1",
            title="Compression running socks",
            store="Runner",
            price=15.0,
            average_rating=4.7,
            rating_number=300,
            main_category="AMAZON FASHION",
            search_text="Compression running socks athletic moisture wicking training",
        )
    ]
    build_index(products, HashingEmbedder(), tmp_path, source_path=tmp_path / "sample.jsonl.gz")

    from app import main

    monkeypatch.setattr(main, "INDEX_PATH", tmp_path)
    monkeypatch.setattr(main, "INDEX_CACHE", None)
    client = TestClient(main.app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["index_ready"] is True

    response = client.post(
        "/recommend",
        json={"query": "running socks for training", "top_k": 1, "filters": {}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"][0]["parent_asin"] == "RUN1"


def test_required_openai_without_key_returns_service_error(monkeypatch, tmp_path) -> None:
    products = [
        ProductRecord(
            parent_asin="RUN1",
            title="Compression running socks",
            store="Runner",
            price=15.0,
            average_rating=4.7,
            rating_number=300,
            main_category="AMAZON FASHION",
            search_text="Compression running socks athletic moisture wicking training",
        )
    ]
    build_index(products, HashingEmbedder(), tmp_path, source_path=tmp_path / "sample.jsonl.gz")

    from app import config, main

    monkeypatch.setattr(main, "INDEX_PATH", tmp_path)
    monkeypatch.setattr(main, "INDEX_CACHE", None)
    monkeypatch.setattr(config, "REQUIRE_OPENAI", True)
    monkeypatch.setattr(config, "OPENAI_API_KEY", "")
    monkeypatch.setattr(config, "USE_LLM", "auto")
    client = TestClient(main.app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "misconfigured"
    assert health.json()["llm_required"] is True

    response = client.post(
        "/recommend",
        json={"query": "running socks for training", "top_k": 1, "filters": {}},
    )

    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]
