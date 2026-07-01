from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is optional at import time
    load_dotenv = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if load_dotenv is not None:
    load_dotenv(PROJECT_ROOT / ".env")


def _path_from_env(name: str, default: Path) -> Path:
    value = os.getenv(name)
    if not value:
        return default
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _flag_from_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


DATASET_PATH = _path_from_env(
    "DATASET_PATH", PROJECT_ROOT / "meta_Amazon_Fashion.jsonl.gz"
)
INDEX_DIR = _path_from_env("INDEX_DIR", PROJECT_ROOT / "data" / "index")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
USE_LLM = os.getenv("USE_LLM", "auto").strip().lower()
REQUIRE_OPENAI = _flag_from_env("REQUIRE_OPENAI") or USE_LLM in {
    "always",
    "openai",
    "required",
    "require",
}

EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "auto").strip().lower()
LOCAL_EMBEDDING_MODEL = os.getenv(
    "LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
).strip()
