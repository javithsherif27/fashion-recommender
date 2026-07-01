# Semantic Fashion Recommendation Microservice

This is a compact take-home implementation for semantic product recommendations over the Amazon Fashion metadata dataset.

The service accepts natural-language shopping requests such as:

```text
I need an outfit to go to the beach this summer
```

It returns product recommendations from the included local vector index with scores and short explanations.

## What Is Included

- FastAPI microservice with `GET /health`, `POST /recommend`, and a small browser demo.
- CLI for local recommendation checks.
- Dataset ingestion and vector index builder.
- Optional OpenAI query interpretation when `OPENAI_API_KEY` is configured.
- Local fallback path that works without any API key.
- Architecture diagram in draw.io and JPEG formats.
- Prebuilt 16,000-product index under `data/index` so the app can run immediately after dependency installation.
- Tests for ingestion, search, and API behavior.

## Setup

```powershell
cd D:\source-code\2026\ProdaptAssignment\ProdaptAssignment
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt
```

For stronger local semantic embeddings, install the optional transformer dependency:

```powershell
.\.venv\Scripts\pip install -r requirements-semantic.txt
```

The app still works without this optional dependency by using the built-in local hashing embedder.

## Optional OpenAI Configuration

Do not hardcode keys in source code. Add a local `.env` file or set environment variables:

```powershell
$env:OPENAI_API_KEY="your-key-here"
$env:OPENAI_MODEL="gpt-4o-mini"
$env:USE_LLM="auto"
```

Behavior:

- If `OPENAI_API_KEY` is present, the service uses OpenAI to turn natural-language requests into richer product search intent and to improve result explanations.
- If the key is missing or an API call fails, the service falls back to local query expansion and local vector search.

## Index

The submitted folder already includes a prebuilt local index:

- `data/index/embeddings.npy`
- `data/index/products.jsonl`
- `data/index/manifest.json`

That is enough to run the API, CLI, tests, and browser demo without downloading the raw dataset.

To rebuild the index, download the Amazon Fashion metadata file from the assignment link into the project root as `meta_Amazon_Fashion.jsonl.gz`, then run:

```powershell
.\.venv\Scripts\python scripts\build_index.py --input meta_Amazon_Fashion.jsonl.gz --index-dir data\index --max-records 16000
```

Use `--max-records 0` to build against the full dataset. By default, the builder tries `sentence-transformers` first and falls back to the local hashing embedder if the optional package is not installed.

## Run The API

```powershell
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

Open the local UI:

```text
http://127.0.0.1:8000
```

The UI is served by the same FastAPI app. It lets a reviewer enter a natural-language shopping request, choose result count, optionally add price/rating filters, and see recommendations from the local index.

## API Usage

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/recommend `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"query":"I need an outfit to go to the beach this summer","top_k":5,"filters":{"max_price":50,"min_rating":4.0}}'
```

Response shape:

```json
{
  "query": "I need an outfit to go to the beach this summer",
  "interpreted_query": "I need an outfit to go to the beach this summer sandals flip flops swimwear shorts lightweight",
  "llm_used": false,
  "llm_provider": "local",
  "embedding_backend": "hashing",
  "recommendations": [
    {
      "parent_asin": "B072826WWT",
      "title": "Summer Pineapple Graphic Tank Tops for Women Funny Cute Vacation Sleeveless Letter Print Tank Top Shirts",
      "store": "JINTING",
      "price": 8.99,
      "average_rating": 4.4,
      "rating_number": 55,
      "score": 0.62,
      "why": "Matches the shopping intent through: beach, summer, lightweight, breathable."
    }
  ],
  "latency_ms": 35
}
```

Actual product results depend on the index size and embedding backend used.

## CLI Usage

```powershell
.\.venv\Scripts\python -m app.cli recommend "comfortable running socks for training" --top-k 5 --min-rating 4
```

## Architecture

The high-level flow is:

```text
Dataset -> ingestion -> embeddings -> vector index
User query -> optional OpenAI interpretation -> vector search -> rerank/filter -> recommendations
```

Diagram files:

- `docs/architecture.drawio`
- `docs/architecture.jpg`

## Design Decisions

- The app is intentionally small: FastAPI, local files, and numpy vector search are enough for a reviewable prototype.
- The OpenAI layer is optional because reviewers should be able to run the submission without a secret key.
- The local fallback includes query expansion for common fashion intents like beach, summer, running, office, wedding, winter, and travel.
- `categories` are not used as a primary signal because the inspected Amazon Fashion file has empty category arrays for the sampled rows.
- The vector index is file-based for simplicity. A production version would move embeddings into a vector database and add background indexing.

## Data Notes

The Amazon Fashion metadata contains 826,108 rows. Many rows have title, store, rating, image, and product-detail fields; fewer rows have price and long descriptions. The ingestion code therefore builds product text from title, features, description, store, and selected detail fields.

## Tests

```powershell
.\.venv\Scripts\pytest
```
