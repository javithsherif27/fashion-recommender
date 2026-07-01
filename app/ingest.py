from __future__ import annotations

import gzip
import json
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.text_utils import compact_text

DETAIL_KEYS = (
    "Department",
    "Fabric type",
    "Material",
    "Outer material",
    "Sole material",
    "Closure type",
    "Care instructions",
    "Fit type",
    "Pattern",
    "Style",
    "Country of Origin",
)


@dataclass(slots=True)
class ProductRecord:
    parent_asin: str
    title: str
    store: str | None
    price: float | None
    average_rating: float | None
    rating_number: int | None
    main_category: str | None
    search_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_price(value: Any) -> float | None:
    if value in (None, "", "None"):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace("$", "").replace(",", "").strip())
    except ValueError:
        return None


def parse_int(value: Any) -> int | None:
    if value in (None, "", "None"):
        return None
    try:
        return int(float(str(value).replace(",", "").strip()))
    except ValueError:
        return None


def parse_float(value: Any) -> float | None:
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def product_text(row: dict[str, Any]) -> str:
    details = row.get("details") or {}
    detail_parts: list[str] = []
    if isinstance(details, dict):
        for key in DETAIL_KEYS:
            value = details.get(key)
            if value:
                detail_parts.append(f"{key}: {value}")

    features = row.get("features") or []
    description = row.get("description") or []
    categories = row.get("categories") or []

    return compact_text(
        [
            row.get("title"),
            row.get("store"),
            categories[:4] if isinstance(categories, list) else categories,
            features[:8] if isinstance(features, list) else features,
            description[:3] if isinstance(description, list) else description,
            detail_parts,
        ]
    )


def row_to_product(row: dict[str, Any]) -> ProductRecord | None:
    title = compact_text([row.get("title")], max_chars=300)
    asin = compact_text([row.get("parent_asin")], max_chars=80)
    text = product_text(row)
    if not title or not asin or len(text) < 8:
        return None
    return ProductRecord(
        parent_asin=asin,
        title=title,
        store=compact_text([row.get("store")], max_chars=120) or None,
        price=parse_price(row.get("price")),
        average_rating=parse_float(row.get("average_rating")),
        rating_number=parse_int(row.get("rating_number")),
        main_category=compact_text([row.get("main_category")], max_chars=120) or None,
        search_text=text,
    )


def iter_products(path: Path, limit: int | None = None) -> Iterator[ProductRecord]:
    yielded = 0
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}") from exc
            product = row_to_product(row)
            if product is None:
                continue
            yield product
            yielded += 1
            if limit is not None and yielded >= limit:
                break

