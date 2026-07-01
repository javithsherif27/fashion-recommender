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

FASHION_REQUEST_TERMS = {
    "accessory",
    "activewear",
    "athletic",
    "beach",
    "beanie",
    "belt",
    "bikini",
    "blazer",
    "boots",
    "bra",
    "business",
    "cap",
    "cardigan",
    "casual",
    "clothes",
    "clothing",
    "coat",
    "cotton",
    "dress",
    "fleece",
    "flip",
    "formal",
    "gloves",
    "gown",
    "gym",
    "hat",
    "hoodie",
    "interview",
    "jacket",
    "jeans",
    "jogger",
    "leggings",
    "linen",
    "men",
    "mens",
    "men's",
    "office",
    "outfit",
    "pants",
    "party",
    "rain",
    "running",
    "sandal",
    "sandals",
    "scarf",
    "shirt",
    "shoes",
    "shorts",
    "ski",
    "sneakers",
    "socks",
    "sports",
    "summer",
    "sweater",
    "sweatpants",
    "sweatshirt",
    "swimwear",
    "tank",
    "tee",
    "thermal",
    "top",
    "travel",
    "trousers",
    "wear",
    "wedding",
    "winter",
    "women",
    "womens",
    "women's",
    "workout",
    "yoga",
}

FASHION_PRODUCT_TERMS = FASHION_REQUEST_TERMS - {
    "beach",
    "business",
    "casual",
    "interview",
    "men",
    "mens",
    "men's",
    "office",
    "party",
    "rain",
    "running",
    "ski",
    "sports",
    "summer",
    "travel",
    "wedding",
    "winter",
    "women",
    "womens",
    "women's",
    "workout",
    "yoga",
}

FASHION_CONTEXT_TERMS = FASHION_REQUEST_TERMS - FASHION_PRODUCT_TERMS

FASHION_ATTRIBUTE_TERMS = {
    "beige",
    "black",
    "blue",
    "bright",
    "brown",
    "burgundy",
    "camouflage",
    "camo",
    "cream",
    "floral",
    "gold",
    "gray",
    "green",
    "grey",
    "khaki",
    "navy",
    "orange",
    "pastel",
    "pink",
    "plaid",
    "purple",
    "red",
    "silver",
    "striped",
    "tan",
    "teal",
    "white",
    "yellow",
}

SHOPPING_INTENT_TERMS = {
    "buy",
    "find",
    "for",
    "looking",
    "need",
    "recommend",
    "search",
    "shop",
    "show",
    "suggest",
    "want",
    "wear",
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


def is_fashion_request(query: str) -> bool:
    tokens = set(tokenize(query))
    if not tokens:
        return False
    if tokens & FASHION_PRODUCT_TERMS:
        return True
    has_attribute_terms = bool(tokens & FASHION_ATTRIBUTE_TERMS)
    if has_attribute_terms and tokens <= FASHION_ATTRIBUTE_TERMS:
        return True
    has_shopping_intent = bool(tokens & SHOPPING_INTENT_TERMS)
    has_fashion_context = bool(tokens & FASHION_CONTEXT_TERMS)
    has_descriptive_context = any(
        term in query.lower()
        for term in (
            "what should i wear",
            "what to wear",
            "dress code",
            "outdoor",
            "warm weather",
            "cold weather",
        )
    )
    return has_shopping_intent and (
        has_fashion_context or has_attribute_terms or has_descriptive_context
    )


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
