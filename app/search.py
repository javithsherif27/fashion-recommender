from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from app.embedding import Embedder, create_embedder
from app.ingest import ProductRecord
from app.llm import LocalQueryInterpreter
from app.models import ProductFilters
from app.text_utils import FASHION_PRODUCT_TERMS, is_fashion_request, shared_query_terms, tokenize


BROAD_PRODUCT_TERMS = {
    "accessories",
    "accessory",
    "activewear",
    "apparel",
    "clothes",
    "clothing",
    "costume",
    "fashion",
    "footwear",
    "jewelry",
    "outfit",
}

SPECIFIC_PRODUCT_TERMS = FASHION_PRODUCT_TERMS - BROAD_PRODUCT_TERMS

PRODUCT_TERM_ALIASES = {
    "coat": {"coat", "coats", "jacket", "jackets", "parka", "parkas"},
    "jacket": {"coat", "coats", "jacket", "jackets", "parka", "parkas"},
    "shoe": {"shoe", "shoes", "sneaker", "sneakers", "loafer", "loafers", "oxford", "oxfords"},
    "shoes": {"shoe", "shoes", "sneaker", "sneakers", "loafer", "loafers", "oxford", "oxfords"},
    "sneaker": {"shoe", "shoes", "sneaker", "sneakers", "trainer", "trainers"},
    "sneakers": {"shoe", "shoes", "sneaker", "sneakers", "trainer", "trainers"},
    "t-shirt": {"t-shirt", "tshirt", "tee", "shirt", "top"},
    "tee": {"t-shirt", "tshirt", "tee", "shirt", "top"},
    "top": {"top", "tops", "blouse", "blouses", "shirt", "shirts", "tee", "t-shirt"},
}


class ProductIndex:
    def __init__(
        self,
        products: list[dict[str, Any]],
        embeddings: np.ndarray,
        embedder: Embedder,
        manifest: dict[str, Any],
    ) -> None:
        self.products = products
        self.embeddings = embeddings.astype(np.float32)
        self.embedder = embedder
        self.manifest = manifest

    @classmethod
    def load(cls, index_dir: Path) -> "ProductIndex":
        manifest_path = index_dir / "manifest.json"
        metadata_path = index_dir / "products.jsonl"
        embeddings_path = index_dir / "embeddings.npy"
        if not manifest_path.exists() or not metadata_path.exists() or not embeddings_path.exists():
            raise FileNotFoundError(
                f"Index not found in {index_dir}. Run scripts/build_index.py first."
            )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        embedder = create_embedder(manifest.get("embedding_backend", "hashing"))
        products = [
            json.loads(line)
            for line in metadata_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        embeddings = np.load(embeddings_path)
        return cls(products=products, embeddings=embeddings, embedder=embedder, manifest=manifest)

    def recommend(
        self,
        query: str,
        *,
        top_k: int,
        filters: ProductFilters,
        interpreter: LocalQueryInterpreter,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        intent = interpreter.interpret(query)
        if not is_fashion_request(query):
            return {
                "query": query,
                "interpreted_query": intent.search_query,
                "llm_used": intent.llm_used,
                "llm_provider": intent.provider,
                "embedding_backend": self.embedder.backend,
                "recommendations": [],
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "message": (
                    "This service is scoped to fashion product recommendations. "
                    "Try a clothing item, accessory, season, occasion, or audience request."
                ),
            }
        requested_gender = _requested_gender(query)
        query_vector = self.embedder.encode([intent.search_query], is_query=True)[0]
        similarities = self.embeddings @ query_vector
        candidate_count = min(len(similarities), max(top_k * 500, 5000))
        candidate_indexes = np.argpartition(-similarities, candidate_count - 1)[:candidate_count]
        ordered = candidate_indexes[np.argsort(-similarities[candidate_indexes])]

        candidates: list[dict[str, Any]] = []
        seen_asins: set[str] = set()
        for index in ordered:
            product = self.products[int(index)]
            asin = str(product.get("parent_asin"))
            if asin in seen_asins:
                continue
            if not _passes_filters(product, filters):
                continue
            if _contains_avoid_terms(product.get("search_text", ""), intent.avoid):
                continue
            product_text = f"{product.get('title', '')} {product.get('search_text', '')}"
            if _conflicts_with_requested_audience(query, requested_gender, product_text):
                continue
            seen_asins.add(asin)
            similarity = float(similarities[int(index)])
            quality_boost = _quality_boost(product)
            matched_terms = shared_query_terms(intent.search_query, product.get("search_text", ""))
            semantic_adjustment = _semantic_adjustment(
                query,
                intent.search_query,
                product,
                matched_terms,
                requested_gender,
            )
            score = round(
                min(1.0, max(0.0, similarity + quality_boost + semantic_adjustment)),
                4,
            )
            why = _default_reason(matched_terms, product)
            candidates.append(
                {
                    **_public_product_fields(product),
                    "score": score,
                    "why": why,
                    "matched_terms": matched_terms,
                }
            )

        selected = sorted(candidates, key=lambda item: item["score"], reverse=True)[:top_k]

        llm_reasons = interpreter.explain_results(query, selected)
        for item, reason in zip(selected, llm_reasons, strict=False):
            if reason:
                item["why"] = reason

        for item in selected:
            item.pop("matched_terms", None)

        elapsed = int((time.perf_counter() - started) * 1000)
        return {
            "query": query,
            "interpreted_query": intent.search_query,
            "llm_used": intent.llm_used,
            "llm_provider": intent.provider,
            "embedding_backend": self.embedder.backend,
            "recommendations": selected,
            "latency_ms": elapsed,
            "message": None,
        }


def build_index(
    products: list[ProductRecord],
    embedder: Embedder,
    index_dir: Path,
    *,
    source_path: Path,
    batch_size: int = 128,
) -> dict[str, Any]:
    index_dir.mkdir(parents=True, exist_ok=True)
    texts = [product.search_text for product in products]
    chunks: list[np.ndarray] = []
    for start in range(0, len(texts), batch_size):
        chunks.append(embedder.encode(texts[start : start + batch_size]))
    embeddings = np.vstack(chunks) if chunks else np.empty((0, embedder.dimensions), dtype=np.float32)
    np.save(index_dir / "embeddings.npy", embeddings.astype(np.float32))

    with (index_dir / "products.jsonl").open("w", encoding="utf-8") as handle:
        for product in products:
            handle.write(json.dumps(asdict(product), ensure_ascii=False) + "\n")

    manifest = {
        "source_path": str(source_path),
        "product_count": len(products),
        "embedding_backend": embedder.backend,
        "embedding_model": embedder.model_name,
        "dimensions": embedder.dimensions,
        "created_by": "scripts/build_index.py",
    }
    (index_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


def _passes_filters(product: dict[str, Any], filters: ProductFilters) -> bool:
    price = product.get("price")
    rating = product.get("average_rating")
    if filters.require_price and price is None:
        return False
    if filters.max_price is not None:
        if price is None or float(price) > filters.max_price:
            return False
    if filters.min_rating is not None:
        if rating is None or float(rating) < filters.min_rating:
            return False
    return True


def _contains_avoid_terms(text: str, avoid_terms: list[str]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in avoid_terms)


def _quality_boost(product: dict[str, Any]) -> float:
    rating = float(product.get("average_rating") or 0)
    rating_number = float(product.get("rating_number") or 0)
    rating_boost = max(0.0, rating - 3.5) * 0.015
    popularity_boost = min(np.log1p(rating_number) / 100.0, 0.08)
    return rating_boost + popularity_boost


def _semantic_adjustment(
    original_query: str,
    interpreted_query: str,
    product: dict[str, Any],
    matched_terms: list[str],
    requested_gender: str | None = None,
) -> float:
    query_lower = original_query.lower()
    interpreted_lower = interpreted_query.lower()
    text = f"{product.get('title', '')} {product.get('search_text', '')}".lower()

    boost = min(0.18, len(set(matched_terms)) * 0.025)
    requested_product_terms = _requested_product_terms(original_query)
    if requested_product_terms:
        title = str(product.get("title") or "").lower()
        title_tokens = set(tokenize(title))
        matched_product_terms = [
            term
            for term in requested_product_terms
            if _term_matches_product_title(term, title_tokens, title)
        ]
        if matched_product_terms:
            boost += min(0.3, len(matched_product_terms) * 0.14)
        else:
            boost -= 0.34

    product_gender = _product_gender(text)
    if requested_gender is not None:
        if product_gender == requested_gender:
            boost += 0.08
        elif product_gender == "unisex":
            boost += 0.03

    summer_or_beach = any(term in interpreted_lower for term in ("beach", "summer", "swim"))
    if summer_or_beach:
        apparel_terms = (
            "sandal",
            "flip flop",
            "shorts",
            "dress",
            "tank top",
            "swim",
            "bikini",
            "cover up",
            "linen",
            "palazzo",
            "romper",
            "shirt",
            "tee",
        )
        accessory_terms = ("hat", "cap", "belt", "wallet", "watch", "jewelry")
        off_intent_terms = (
            "costume",
            "gothic",
            "medieval",
            "renaissance",
            "cosplay",
            "wedding",
            "formal",
        )
        if any(term in text for term in apparel_terms):
            boost += 0.12
        if "outfit" in query_lower and any(term in text for term in apparel_terms):
            boost += 0.08
        if "beach" in text:
            boost += 0.08
        if "summer" in text:
            boost += 0.05
        explicit_accessory_query = any(term in query_lower for term in accessory_terms)
        if (
            any(term in text for term in accessory_terms)
            and not any(term in text for term in apparel_terms)
            and not explicit_accessory_query
        ):
            boost -= 0.22
        if any(term in text for term in ("hoodie", "sweatshirt", "thermal", "fleece")):
            boost -= 0.15
        if any(term in text for term in off_intent_terms):
            boost -= 0.16

    if "outfit" in query_lower and not any(
        child_term in query_lower for child_term in ("baby", "kid", "kids", "toddler", "girl")
    ):
        if any(child_term in text for child_term in ("baby", "toddler", "infant", "kids")):
            boost -= 0.08

    return boost


def _requested_product_terms(query: str) -> set[str]:
    lower = query.lower()
    terms = set(tokenize(lower)) & SPECIFIC_PRODUCT_TERMS
    if "black tie" in lower:
        terms.discard("tie")
    return terms


def _term_matches_product_title(term: str, title_tokens: set[str], title: str) -> bool:
    candidates = set(PRODUCT_TERM_ALIASES.get(term, (term,)))
    candidates.add(term)
    if term.endswith("s") and len(term) > 3:
        candidates.add(term[:-1])
    else:
        candidates.add(f"{term}s")
    candidates.add(term.replace("-", " "))
    return bool(candidates & title_tokens) or any(f" {candidate} " in f" {title} " for candidate in candidates)


def _requested_gender(query: str) -> str | None:
    text = query.lower()
    tokens = set(tokenize(text))
    men_markers = {"men", "mens", "men's", "male", "man", "boys", "boy"}
    women_markers = {"women", "womens", "women's", "female", "woman", "ladies", "lady", "girls", "girl"}
    asks_men = bool(tokens & men_markers) or any(
        phrase in text for phrase in ("for men", "mens ", "men's ", "male ")
    )
    asks_women = bool(tokens & women_markers) or any(
        phrase in text for phrase in ("for women", "womens ", "women's ", "ladies ")
    )
    if asks_men and not asks_women:
        return "men"
    if asks_women and not asks_men:
        return "women"
    return None


def _product_gender(text: str) -> str | None:
    tokens = set(tokenize(text))
    men_markers = {"men", "mens", "men's", "male", "man", "boys", "boy"}
    women_markers = {"women", "womens", "women's", "female", "woman", "ladies", "lady", "girls", "girl"}
    has_men = bool(tokens & men_markers)
    has_women = bool(tokens & women_markers)
    if has_men and has_women:
        return "unisex"
    if has_men:
        return "men"
    if has_women:
        return "women"
    return None


def _conflicts_with_requested_audience(
    query: str,
    requested_gender: str | None,
    product_text: str,
) -> bool:
    query_tokens = set(tokenize(query))
    child_markers = {
        "baby",
        "babies",
        "boy",
        "boy's",
        "boys",
        "child",
        "children",
        "girl",
        "girl's",
        "girls",
        "infant",
        "kid",
        "kids",
        "toddler",
    }
    product_tokens = set(tokenize(product_text))
    if not (query_tokens & child_markers) and product_tokens & child_markers:
        return True
    if requested_gender is None:
        return False
    product_gender = _product_gender(product_text)
    return (requested_gender == "men" and product_gender == "women") or (
        requested_gender == "women" and product_gender == "men"
    )


def _default_reason(matched_terms: list[str], product: dict[str, Any]) -> str:
    if matched_terms:
        terms = ", ".join(matched_terms[:4])
        return f"Matches the shopping intent through: {terms}."
    rating = product.get("average_rating")
    if rating:
        return f"Recommended by semantic similarity and a {rating} average rating."
    return "Recommended by semantic similarity to the query."


def _public_product_fields(product: dict[str, Any]) -> dict[str, Any]:
    return {
        "parent_asin": product.get("parent_asin"),
        "title": product.get("title"),
        "store": product.get("store"),
        "price": product.get("price"),
        "average_rating": product.get("average_rating"),
        "rating_number": product.get("rating_number"),
    }
