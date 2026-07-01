from __future__ import annotations

import pytest

from app.text_utils import expand_query_text, infer_avoid_terms, is_fashion_request


@pytest.mark.parametrize(
    "query",
    [
        "blue pink",
        "linen shirt",
        "gold earrings",
        "leather wallet",
        "waterproof hiking boots",
        "black tie wedding outfit",
        "date night",
        "maternity wear",
        "plus size cotton kurti",
        "petite formal trousers",
        "kids school shoes",
        "men",
        "women",
        "what should I wear to a beach wedding",
        "what to wear for office interview",
        "show me red floral",
        "running socks under 20",
        "modest ethnic festival dress",
        "winter travel clothes",
        "sunglasses",
        "cotton slim fit",
    ],
)
def test_valid_fashion_query_shapes_are_allowed(query: str) -> None:
    assert is_fashion_request(query)


@pytest.mark.parametrize(
    "query",
    [
        "what is Indias national anthem",
        "what is blue light",
        "what is international women day",
        "international women day",
        "how to cook rice",
        "taj hotels",
        "weather today",
        "python list comprehension",
        "gift for brother",
        "under 50",
    ],
)
def test_non_fashion_query_shapes_are_blocked(query: str) -> None:
    assert not is_fashion_request(query)


def test_query_expansion_supports_common_contexts() -> None:
    expanded = expand_query_text("black tie wedding")

    assert "tuxedo" in expanded
    assert "dress shoes" in expanded


def test_avoid_terms_cover_conflicting_contexts() -> None:
    avoid = infer_avoid_terms("maternity winter wear")

    assert "swimwear" in avoid
    assert "corset" in avoid
