from __future__ import annotations

import re
from collections.abc import Iterable

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9'+-]*")

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "for",
    "go",
    "i",
    "in",
    "it",
    "need",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
}

FASHION_EXPANSIONS: dict[str, tuple[str, ...]] = {
    "beach": (
        "sandals",
        "flip flops",
        "swimwear",
        "swimsuit",
        "shorts",
        "sun hat",
        "lightweight",
        "summer",
        "breathable",
    ),
    "summer": (
        "lightweight",
        "breathable",
        "cotton",
        "linen",
        "shorts",
        "sandals",
        "tank top",
        "dress",
    ),
    "running": (
        "athletic",
        "compression",
        "moisture wicking",
        "sneakers",
        "socks",
        "leggings",
        "workout",
    ),
    "gym": (
        "athletic",
        "workout",
        "yoga",
        "leggings",
        "sports bra",
        "moisture wicking",
        "training",
    ),
    "office": (
        "business",
        "formal",
        "dress shirt",
        "trousers",
        "blazer",
        "work",
    ),
    "interview": (
        "business",
        "formal",
        "dress shirt",
        "blazer",
        "professional",
        "work",
    ),
    "wedding": (
        "dress",
        "gown",
        "formal",
        "heels",
        "jewelry",
        "party",
    ),
    "party": (
        "dress",
        "heels",
        "jewelry",
        "evening",
        "gown",
        "formal",
    ),
    "winter": (
        "coat",
        "jacket",
        "thermal",
        "fleece",
        "boots",
        "warm",
    ),
    "rain": (
        "waterproof",
        "rain jacket",
        "boots",
        "poncho",
        "weather",
    ),
    "travel": (
        "comfortable",
        "lightweight",
        "casual",
        "sneakers",
        "backpack",
        "wrinkle resistant",
    ),
}


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def compact_text(parts: Iterable[object], max_chars: int = 2400) -> str:
    cleaned: list[str] = []
    for part in parts:
        if part is None:
            continue
        if isinstance(part, (list, tuple)):
            cleaned.extend(str(item).strip() for item in part if str(item).strip())
        else:
            value = str(part).strip()
            if value:
                cleaned.append(value)
    text = " ".join(cleaned)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def expand_query_text(query: str) -> str:
    lower = query.lower()
    additions: list[str] = []
    tokens = set(tokenize(query))
    for trigger, terms in FASHION_EXPANSIONS.items():
        if trigger in tokens or trigger in lower:
            additions.extend(terms)
    if not additions:
        return query
    return f"{query} {' '.join(dict.fromkeys(additions))}"


def infer_avoid_terms(query: str) -> list[str]:
    lower = query.lower()
    tokens = set(tokenize(query))
    avoid: list[str] = []
    if {"beach", "summer"} & tokens or "beach" in lower or "summer" in lower:
        avoid.extend(["winter", "thermal", "fleece", "snow", "ski", "coat", "gloves"])
    if {"office", "interview"} & tokens or "office" in lower or "interview" in lower:
        avoid.extend(["beach", "swimwear", "flip flops", "costume"])
    if {"running", "gym", "workout"} & tokens or "running" in lower or "gym" in lower:
        avoid.extend(["formal", "wedding", "gown", "dress shirt"])
    return list(dict.fromkeys(avoid))


def shared_query_terms(query: str, product_text: str, max_terms: int = 5) -> list[str]:
    product_tokens = set(tokenize(product_text))
    terms: list[str] = []
    for token in tokenize(expand_query_text(query)):
        if len(token) < 3 or token in STOPWORDS:
            continue
        if token in product_tokens and token not in terms:
            terms.append(token)
        if len(terms) >= max_terms:
            break
    return terms
