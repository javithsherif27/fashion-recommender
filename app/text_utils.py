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
    "me",
    "my",
    "need",
    "of",
    "on",
    "or",
    "please",
    "some",
    "something",
    "that",
    "the",
    "this",
    "to",
    "with",
}

FASHION_EXPANSIONS: dict[str, tuple[str, ...]] = {
    "activewear": ("athletic", "workout", "moisture wicking", "leggings", "sneakers"),
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
    "black tie": ("formal", "gown", "suit", "tuxedo", "heels", "dress shoes"),
    "black-tie": ("formal", "gown", "suit", "tuxedo", "heels", "dress shoes"),
    "business": ("formal", "dress shirt", "trousers", "blazer", "office", "work"),
    "casual": ("comfortable", "cotton", "jeans", "t-shirt", "sneakers", "everyday"),
    "cocktail": ("party", "dress", "heels", "jewelry", "evening", "formal"),
    "college": ("casual", "backpack", "sneakers", "hoodie", "jeans", "comfortable"),
    "date": ("date night", "dress", "shirt", "heels", "jewelry", "smart casual"),
    "ethnic": ("traditional", "saree", "kurta", "kurti", "lehenga", "sherwani"),
    "festival": ("ethnic", "traditional", "kurta", "saree", "lehenga", "jewelry"),
    "formal": ("business", "office", "blazer", "dress shirt", "trousers", "dress shoes"),
    "gym": (
        "athletic",
        "workout",
        "yoga",
        "leggings",
        "sports bra",
        "moisture wicking",
        "training",
    ),
    "hiking": ("waterproof", "jacket", "boots", "thermal", "fleece", "outdoor"),
    "interview": (
        "business",
        "formal",
        "dress shirt",
        "blazer",
        "professional",
        "work",
    ),
    "maternity": ("comfortable", "stretch", "dress", "leggings", "nursing", "pregnancy"),
    "monsoon": ("rain", "waterproof", "rain jacket", "boots", "quick dry", "poncho"),
    "office": (
        "business",
        "formal",
        "dress shirt",
        "trousers",
        "blazer",
        "work",
    ),
    "party": (
        "dress",
        "heels",
        "jewelry",
        "evening",
        "gown",
        "formal",
    ),
    "petite": ("short length", "tailored", "dress", "pants", "fit"),
    "plus": ("plus size", "curve", "stretch", "comfortable", "fit"),
    "prom": ("formal", "gown", "dress", "heels", "jewelry", "evening"),
    "rain": (
        "waterproof",
        "rain jacket",
        "boots",
        "poncho",
        "weather",
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
    "school": ("uniform", "shoes", "socks", "backpack", "kids", "comfortable"),
    "ski": ("snow", "waterproof", "thermal", "fleece", "gloves", "jacket", "boots"),
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
    "travel": (
        "comfortable",
        "lightweight",
        "casual",
        "sneakers",
        "backpack",
        "wrinkle resistant",
    ),
    "vacation": ("travel", "summer", "lightweight", "sandals", "shorts", "swimwear"),
    "wedding": (
        "dress",
        "gown",
        "formal",
        "heels",
        "jewelry",
        "party",
    ),
    "winter": (
        "coat",
        "jacket",
        "thermal",
        "fleece",
        "boots",
        "warm",
    ),
    "workout": ("athletic", "gym", "training", "leggings", "socks", "sneakers"),
    "yoga": ("leggings", "sports bra", "stretch", "workout", "athletic", "comfortable"),
}

FASHION_PRODUCT_TERMS = {
    "accessories",
    "accessory",
    "activewear",
    "anklet",
    "apparel",
    "backpack",
    "bag",
    "ballerina",
    "base-layer",
    "baselayer",
    "beanie",
    "belt",
    "bikini",
    "blazer",
    "blouse",
    "boots",
    "boot",
    "bowtie",
    "bra",
    "bracelet",
    "briefs",
    "camisole",
    "cap",
    "cardigan",
    "chinos",
    "clogs",
    "clothes",
    "clothing",
    "coat",
    "costume",
    "crocs",
    "dress",
    "earrings",
    "espadrilles",
    "eyewear",
    "flats",
    "flip",
    "flop",
    "flops",
    "footwear",
    "gloves",
    "gown",
    "hairband",
    "handbag",
    "hat",
    "headband",
    "heels",
    "hoodie",
    "hosiery",
    "jacket",
    "jeans",
    "jewelry",
    "jogger",
    "joggers",
    "jumpsuit",
    "kurta",
    "kurti",
    "lehenga",
    "leggings",
    "lingerie",
    "loafers",
    "moccasins",
    "necklace",
    "nightgown",
    "outfit",
    "oxfords",
    "pajama",
    "pajamas",
    "palazzo",
    "panties",
    "pants",
    "parka",
    "polo",
    "poncho",
    "pumps",
    "purse",
    "raincoat",
    "ring",
    "robe",
    "romper",
    "sandal",
    "sandals",
    "saree",
    "sari",
    "scarf",
    "scrubs",
    "sherwani",
    "shirt",
    "shoe",
    "shoes",
    "shorts",
    "skirt",
    "sleepwear",
    "slippers",
    "sneaker",
    "sneakers",
    "socks",
    "suit",
    "sunglasses",
    "sweater",
    "sweatpants",
    "sweatshirt",
    "swimsuit",
    "swimwear",
    "tank",
    "tee",
    "thermal",
    "tie",
    "tights",
    "top",
    "tracksuit",
    "trainers",
    "trouser",
    "trousers",
    "t-shirt",
    "tshirt",
    "tunic",
    "tuxedo",
    "underwear",
    "uniform",
    "vest",
    "waistcoat",
    "wallet",
    "watch",
    "wedges",
}

FASHION_AUDIENCE_TERMS = {
    "adult",
    "baby",
    "boy",
    "boys",
    "bride",
    "bridesmaid",
    "children",
    "dad",
    "female",
    "girl",
    "girls",
    "groom",
    "infant",
    "kid",
    "kids",
    "ladies",
    "lady",
    "male",
    "man",
    "maternity",
    "men",
    "mens",
    "men's",
    "mom",
    "newborn",
    "plus",
    "pregnancy",
    "pregnant",
    "teen",
    "teens",
    "toddler",
    "unisex",
    "woman",
    "women",
    "womens",
    "women's",
}

FASHION_OCCASION_TERMS = {
    "anniversary",
    "beach",
    "birthday",
    "black-tie",
    "bridal",
    "brunch",
    "business",
    "casual",
    "ceremony",
    "church",
    "cocktail",
    "college",
    "concert",
    "date",
    "dinner",
    "engagement",
    "ethnic",
    "evening",
    "festival",
    "formal",
    "graduation",
    "holiday",
    "interview",
    "mosque",
    "night",
    "office",
    "party",
    "prom",
    "reception",
    "school",
    "temple",
    "traditional",
    "vacation",
    "wedding",
    "work",
}

FASHION_ACTIVITY_TERMS = {
    "athletic",
    "basketball",
    "cycling",
    "dance",
    "football",
    "golf",
    "gym",
    "hiking",
    "outdoor",
    "pilates",
    "rain",
    "running",
    "ski",
    "snow",
    "sports",
    "swim",
    "tennis",
    "training",
    "travel",
    "trekking",
    "walking",
    "workout",
    "yoga",
}

FASHION_SEASON_WEATHER_TERMS = {
    "autumn",
    "breathable",
    "cold",
    "dry",
    "fall",
    "fleece",
    "heat",
    "hot",
    "humid",
    "lightweight",
    "monsoon",
    "quick-dry",
    "rain",
    "snow",
    "spring",
    "summer",
    "sun",
    "thermal",
    "warm",
    "waterproof",
    "weather",
    "windproof",
    "winter",
}

FASHION_ATTRIBUTE_TERMS = {
    "animal",
    "beige",
    "black",
    "blue",
    "bright",
    "brown",
    "burgundy",
    "camouflage",
    "camo",
    "checked",
    "chevron",
    "cream",
    "floral",
    "gold",
    "gray",
    "green",
    "grey",
    "khaki",
    "leopard",
    "multicolor",
    "navy",
    "neon",
    "orange",
    "paisley",
    "pastel",
    "pink",
    "plaid",
    "polka",
    "printed",
    "purple",
    "red",
    "silver",
    "solid",
    "striped",
    "tan",
    "teal",
    "tie-dye",
    "white",
    "yellow",
    "zebra",
}

FASHION_MATERIAL_TERMS = {
    "cashmere",
    "chiffon",
    "cotton",
    "denim",
    "faux",
    "lace",
    "leather",
    "linen",
    "mesh",
    "nylon",
    "polyester",
    "rayon",
    "satin",
    "silk",
    "spandex",
    "suede",
    "velvet",
    "viscose",
    "wool",
}

FASHION_FIT_SIZE_TERMS = {
    "ankle",
    "bodycon",
    "bootcut",
    "cropped",
    "curve",
    "fit",
    "fitted",
    "high-waist",
    "loose",
    "maxi",
    "midi",
    "mini",
    "oversized",
    "petite",
    "plus",
    "regular",
    "relaxed",
    "short",
    "size",
    "skinny",
    "slim",
    "straight",
    "stretch",
    "tall",
    "wide",
    "xl",
    "xxl",
}

FASHION_FEATURE_TERMS = {
    "breathable",
    "comfort",
    "comfortable",
    "compression",
    "detachable",
    "durable",
    "elastic",
    "hooded",
    "moisture",
    "non-slip",
    "padded",
    "pockets",
    "quick-dry",
    "seamless",
    "sleeveless",
    "support",
    "thumbholes",
    "warm",
    "water-resistant",
    "waterproof",
    "windproof",
    "wrinkle",
}

FASHION_STYLE_TERMS = {
    "boho",
    "classic",
    "cute",
    "dressy",
    "elegant",
    "everyday",
    "fashion",
    "gothic",
    "minimal",
    "modest",
    "modern",
    "partywear",
    "professional",
    "retro",
    "smart",
    "streetwear",
    "trendy",
    "vintage",
}

FASHION_CONTEXT_TERMS = (
    FASHION_AUDIENCE_TERMS
    | FASHION_OCCASION_TERMS
    | FASHION_ACTIVITY_TERMS
    | FASHION_SEASON_WEATHER_TERMS
    | FASHION_STYLE_TERMS
)

FASHION_DESCRIPTOR_TERMS = (
    FASHION_ATTRIBUTE_TERMS
    | FASHION_AUDIENCE_TERMS
    | FASHION_CONTEXT_TERMS
    | FASHION_FEATURE_TERMS
    | FASHION_FIT_SIZE_TERMS
    | FASHION_MATERIAL_TERMS
)

FASHION_REQUEST_TERMS = FASHION_PRODUCT_TERMS | FASHION_DESCRIPTOR_TERMS

SHOPPING_INTENT_TERMS = {
    "browse",
    "buy",
    "find",
    "for",
    "gift",
    "looking",
    "need",
    "recommend",
    "search",
    "shop",
    "show",
    "suggest",
    "under",
    "want",
    "wear",
}

QUERY_FILLER_TERMS = STOPWORDS | SHOPPING_INTENT_TERMS | {
    "above",
    "affordable",
    "below",
    "best",
    "budget",
    "cheap",
    "dollar",
    "dollars",
    "good",
    "less",
    "luxury",
    "nice",
    "premium",
    "price",
    "rs",
    "rupees",
    "than",
    "usd",
}

GENERAL_QUESTION_TERMS = {
    "am",
    "are",
    "can",
    "could",
    "did",
    "do",
    "does",
    "how",
    "is",
    "should",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
}

FASHION_INTENT_PHRASES = (
    "clothes for",
    "dress code",
    "outfit for",
    "outfit to",
    "what can i wear",
    "what do i wear",
    "what should i wear",
    "what to wear",
    "wear for",
    "wear to",
)


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
    if {"wedding", "formal", "black-tie", "prom"} & tokens or "black tie" in lower:
        avoid.extend(["gym", "workout", "sweatpants", "hoodie", "flip flops"])
    if {"winter", "snow", "ski"} & tokens or "cold weather" in lower:
        avoid.extend(["swimwear", "bikini", "sandals", "summer", "beach"])
    if {"rain", "monsoon"} & tokens or "rain" in lower or "monsoon" in lower:
        avoid.extend(["suede", "silk", "evening gown", "open toe"])
    if {"maternity", "pregnancy", "pregnant"} & tokens:
        avoid.extend(["bodycon", "skinny", "corset", "costume", "gothic", "renaissance", "medieval", "fairy"])
    return list(dict.fromkeys(avoid))


def is_fashion_request(query: str) -> bool:
    lower = query.lower()
    tokens = set(tokenize(query))
    if not tokens:
        return False
    if any(phrase in lower for phrase in FASHION_INTENT_PHRASES):
        return True
    if tokens & FASHION_PRODUCT_TERMS:
        return True

    meaningful_tokens = tokens - QUERY_FILLER_TERMS - GENERAL_QUESTION_TERMS
    if not meaningful_tokens:
        return False

    is_general_question = bool(tokens & GENERAL_QUESTION_TERMS)
    if is_general_question:
        return False

    if meaningful_tokens <= FASHION_DESCRIPTOR_TERMS:
        return True

    has_shopping_intent = bool(tokens & SHOPPING_INTENT_TERMS)
    has_fashion_signal = bool(meaningful_tokens & FASHION_DESCRIPTOR_TERMS)
    return has_shopping_intent and has_fashion_signal


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
