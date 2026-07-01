from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import config
from app.embedding import create_embedder
from app.ingest import iter_products
from app.search import build_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the fashion recommendation index")
    parser.add_argument("--input", type=Path, default=config.DATASET_PATH)
    parser.add_argument("--index-dir", type=Path, default=config.INDEX_DIR)
    parser.add_argument(
        "--max-records",
        type=int,
        default=50000,
        help="Maximum products to index. Use 0 for the full dataset.",
    )
    parser.add_argument("--backend", default=config.EMBEDDING_BACKEND)
    parser.add_argument("--batch-size", type=int, default=128)
    args = parser.parse_args()

    limit = None if args.max_records == 0 else args.max_records
    embedder = create_embedder(args.backend)
    products = list(
        tqdm(
            iter_products(args.input, limit=limit),
            total=limit,
            desc="Reading products",
            unit="product",
        )
    )
    if not products:
        raise SystemExit("No valid products found. Check the dataset path.")
    manifest = build_index(
        products,
        embedder,
        args.index_dir,
        source_path=args.input,
        batch_size=args.batch_size,
    )
    print(f"Built index at {args.index_dir}")
    print(f"Products: {manifest['product_count']}")
    print(f"Embedding backend: {manifest['embedding_backend']}")
    print(f"Embedding model: {manifest['embedding_model']}")


if __name__ == "__main__":
    main()
