from __future__ import annotations

from app.ingest import product_text, row_to_product


def test_product_text_uses_title_features_description_and_details() -> None:
    row = {
        "title": "Lightweight Beach Sandal",
        "store": "Coast Store",
        "features": ["Rubber sole", "Water friendly"],
        "description": ["A casual sandal for summer trips."],
        "details": {"Department": "womens", "Material": "rubber"},
    }

    text = product_text(row)

    assert "Lightweight Beach Sandal" in text
    assert "Water friendly" in text
    assert "summer trips" in text
    assert "Material: rubber" in text


def test_row_to_product_handles_missing_optional_fields() -> None:
    row = {
        "parent_asin": "ASIN1",
        "title": "Compression running socks",
        "average_rating": "4.5",
        "rating_number": "120",
        "price": "$12.99",
    }

    product = row_to_product(row)

    assert product is not None
    assert product.parent_asin == "ASIN1"
    assert product.price == 12.99
    assert product.average_rating == 4.5
    assert product.rating_number == 120

