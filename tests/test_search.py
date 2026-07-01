from __future__ import annotations

from app.embedding import HashingEmbedder
from app.ingest import ProductRecord
from app.llm import LocalQueryInterpreter
from app.models import ProductFilters
from app.search import ProductIndex, build_index


def test_recommend_returns_relevant_products(tmp_path) -> None:
    products = [
        ProductRecord(
            parent_asin="BEACH1",
            title="Water friendly beach sandals",
            store="Coast",
            price=22.0,
            average_rating=4.4,
            rating_number=120,
            main_category="AMAZON FASHION",
            search_text="Water friendly beach sandals for summer trips lightweight breathable",
        ),
        ProductRecord(
            parent_asin="RUN1",
            title="Compression running socks",
            store="Runner",
            price=15.0,
            average_rating=4.7,
            rating_number=300,
            main_category="AMAZON FASHION",
            search_text="Compression running socks athletic moisture wicking training",
        ),
        ProductRecord(
            parent_asin="FORMAL1",
            title="Formal office blazer",
            store="Workwear",
            price=80.0,
            average_rating=4.2,
            rating_number=44,
            main_category="AMAZON FASHION",
            search_text="Formal office blazer professional business work",
        ),
    ]
    build_index(products, HashingEmbedder(), tmp_path, source_path=tmp_path / "sample.jsonl.gz")
    index = ProductIndex.load(tmp_path)

    result = index.recommend(
        "I need something for the beach this summer",
        top_k=1,
        filters=ProductFilters(),
        interpreter=LocalQueryInterpreter(),
    )

    assert result["recommendations"][0]["parent_asin"] == "BEACH1"


def test_recommend_applies_filters(tmp_path) -> None:
    products = [
        ProductRecord(
            parent_asin="A",
            title="Affordable summer sandal",
            store="Coast",
            price=20.0,
            average_rating=4.3,
            rating_number=20,
            main_category="AMAZON FASHION",
            search_text="summer beach sandal lightweight",
        ),
        ProductRecord(
            parent_asin="B",
            title="Luxury summer sandal",
            store="Luxury",
            price=120.0,
            average_rating=4.9,
            rating_number=200,
            main_category="AMAZON FASHION",
            search_text="summer beach sandal lightweight",
        ),
    ]
    build_index(products, HashingEmbedder(), tmp_path, source_path=tmp_path / "sample.jsonl.gz")
    index = ProductIndex.load(tmp_path)

    result = index.recommend(
        "summer beach sandals",
        top_k=2,
        filters=ProductFilters(max_price=50),
        interpreter=LocalQueryInterpreter(),
    )

    assert [item["parent_asin"] for item in result["recommendations"]] == ["A"]


def test_mens_query_excludes_women_only_products(tmp_path) -> None:
    products = [
        ProductRecord(
            parent_asin="WOMEN1",
            title="Women's winter fleece hiking jacket",
            store="Trail",
            price=47.99,
            average_rating=4.8,
            rating_number=500,
            main_category="AMAZON FASHION",
            search_text="Women's winter fleece hiking jacket thermal warm breathable",
        ),
        ProductRecord(
            parent_asin="MEN1",
            title="Men winter fleece jacket",
            store="Trail",
            price=52.0,
            average_rating=4.1,
            rating_number=20,
            main_category="AMAZON FASHION",
            search_text="Men winter fleece jacket coat thermal warm",
        ),
    ]
    build_index(products, HashingEmbedder(), tmp_path, source_path=tmp_path / "sample.jsonl.gz")
    index = ProductIndex.load(tmp_path)

    result = index.recommend(
        "looking for indian winter wear for men",
        top_k=2,
        filters=ProductFilters(),
        interpreter=LocalQueryInterpreter(),
    )

    asins = [item["parent_asin"] for item in result["recommendations"]]
    assert "WOMEN1" not in asins
    assert asins == ["MEN1"]


def test_require_price_excludes_missing_prices(tmp_path) -> None:
    products = [
        ProductRecord(
            parent_asin="NO_PRICE",
            title="Men thermal winter jacket",
            store="Trail",
            price=None,
            average_rating=4.8,
            rating_number=500,
            main_category="AMAZON FASHION",
            search_text="Men thermal winter jacket coat warm fleece",
        ),
        ProductRecord(
            parent_asin="WITH_PRICE",
            title="Men warm winter coat",
            store="Trail",
            price=49.99,
            average_rating=4.0,
            rating_number=10,
            main_category="AMAZON FASHION",
            search_text="Men warm winter coat jacket",
        ),
    ]
    build_index(products, HashingEmbedder(), tmp_path, source_path=tmp_path / "sample.jsonl.gz")
    index = ProductIndex.load(tmp_path)

    result = index.recommend(
        "winter wear for men",
        top_k=2,
        filters=ProductFilters(require_price=True),
        interpreter=LocalQueryInterpreter(),
    )

    assert [item["parent_asin"] for item in result["recommendations"]] == ["WITH_PRICE"]


def test_adult_query_excludes_kids_products(tmp_path) -> None:
    products = [
        ProductRecord(
            parent_asin="BOY1",
            title="Boy's ski jacket waterproof winter coat",
            store="Trail",
            price=69.99,
            average_rating=4.9,
            rating_number=1000,
            main_category="AMAZON FASHION",
            search_text="Boy's ski jacket waterproof winter coat fleece warm",
        ),
        ProductRecord(
            parent_asin="MEN1",
            title="Men winter fleece coat",
            store="Trail",
            price=49.99,
            average_rating=4.1,
            rating_number=20,
            main_category="AMAZON FASHION",
            search_text="Men winter fleece coat warm",
        ),
    ]
    build_index(products, HashingEmbedder(), tmp_path, source_path=tmp_path / "sample.jsonl.gz")
    index = ProductIndex.load(tmp_path)

    result = index.recommend(
        "winter coat for men",
        top_k=2,
        filters=ProductFilters(require_price=True),
        interpreter=LocalQueryInterpreter(),
    )

    assert [item["parent_asin"] for item in result["recommendations"]] == ["MEN1"]


def test_non_fashion_query_returns_no_recommendations(tmp_path) -> None:
    products = [
        ProductRecord(
            parent_asin="GIFT1",
            title="Brother birthday gift tumbler",
            store="Gift Shop",
            price=24.99,
            average_rating=4.6,
            rating_number=88,
            main_category="AMAZON FASHION",
            search_text="Brother birthday gifts cup tumbler best brother gift",
        )
    ]
    build_index(products, HashingEmbedder(), tmp_path, source_path=tmp_path / "sample.jsonl.gz")
    index = ProductIndex.load(tmp_path)

    result = index.recommend(
        "what is Indias national anthem",
        top_k=5,
        filters=ProductFilters(require_price=True),
        interpreter=LocalQueryInterpreter(),
    )

    assert result["recommendations"] == []
    assert result["message"] is not None


def test_audience_word_alone_is_not_fashion_request(tmp_path) -> None:
    products = [
        ProductRecord(
            parent_asin="WOMEN1",
            title="Women's padded sports bra",
            store="Active Shop",
            price=23.99,
            average_rating=4.3,
            rating_number=18,
            main_category="AMAZON FASHION",
            search_text="women sports bra workout activewear",
        )
    ]
    build_index(products, HashingEmbedder(), tmp_path, source_path=tmp_path / "sample.jsonl.gz")
    index = ProductIndex.load(tmp_path)

    result = index.recommend(
        "what is international women day",
        top_k=5,
        filters=ProductFilters(require_price=True),
        interpreter=LocalQueryInterpreter(),
    )

    assert result["recommendations"] == []
    assert result["message"] is not None
