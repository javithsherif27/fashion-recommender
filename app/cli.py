from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app import config
from app.llm import get_interpreter
from app.models import ProductFilters
from app.search import ProductIndex


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Semantic fashion recommender CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    recommend_parser = subparsers.add_parser("recommend", help="Recommend products")
    recommend_parser.add_argument("query", help="Natural-language shopping request")
    recommend_parser.add_argument("--top-k", type=int, default=5)
    recommend_parser.add_argument("--max-price", type=float)
    recommend_parser.add_argument("--min-rating", type=float)
    recommend_parser.add_argument("--index-dir", type=Path, default=config.INDEX_DIR)

    args = parser.parse_args()
    if args.command == "recommend":
        index = ProductIndex.load(args.index_dir)
        result = index.recommend(
            args.query,
            top_k=args.top_k,
            filters=ProductFilters(max_price=args.max_price, min_rating=args.min_rating),
            interpreter=get_interpreter(),
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
