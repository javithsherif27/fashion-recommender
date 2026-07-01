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
- Fashion-domain guard so unrelated questions return a clear scoped message while compact product-attribute searches, such as color combinations, still work.
- Price, rating, listed-price, and audience-aware filtering for cleaner recommendations.
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

The UI is served by the same FastAPI app. It lets a reviewer enter a natural-language shopping request, choose result count, optionally add price/rating filters, require products with a listed price, and see recommendations from the local index. Non-fashion queries return an empty state with a scope message instead of unrelated products.

## Supported Search Criteria

The recommender accepts several fashion shopping query shapes:

- Direct product types: `linen shirt`, `gold earrings`, `waterproof hiking boots`, `leather wallet`.
- Audience/category searches: `men`, `women`, `kids school shoes`, `maternity wear`, `plus size cotton kurti`.
- Occasion and dress-code searches: `office interview outfit`, `date night`, `black tie wedding outfit`, `festival dress`.
- Activity and weather searches: `running socks`, `yoga leggings`, `winter travel clothes`, `rain jacket`.
- Attribute searches: color, pattern, material, fit, size, style, and feature terms such as `blue pink`, `red floral`, `cotton slim fit`, `petite formal trousers`, or `waterproof breathable`.
- Natural language styling questions: `what should I wear to a beach wedding` or `what to wear for office interview`.

General questions and non-shopping text, such as `what is Indias national anthem`, `what is blue light`, or `how to cook rice`, are rejected before vector search.

## API Usage

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/recommend `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"query":"I need an outfit to go to the beach this summer","top_k":5,"filters":{"max_price":50,"min_rating":4.0,"require_price":true}}'
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
  "latency_ms": 35,
  "message": null
}
```

Actual product results depend on the index size and embedding backend used.

For an out-of-domain request, the API returns no products and explains the scope:

```json
{
  "query": "what is Indias national anthem",
  "interpreted_query": "what is Indias national anthem",
  "llm_used": false,
  "llm_provider": "local",
  "embedding_backend": "hashing",
  "recommendations": [],
  "latency_ms": 0,
  "message": "This service is scoped to fashion product recommendations. Try a clothing item, accessory, season, occasion, or audience request."
}
```

## CLI Usage

```powershell
.\.venv\Scripts\python -m app.cli recommend "comfortable running socks for training" --top-k 5 --min-rating 4
```

## Architecture

The high-level flow is:

```text
Dataset -> ingestion -> embeddings -> vector index
User query -> optional OpenAI/local interpretation -> fashion-domain guard -> vector search -> price/audience filters -> rerank/dedupe -> recommendations
Out-of-domain query -> scoped empty response
```

Diagram files:

- `docs/architecture.drawio`
- `docs/architecture.jpg`

## Design Decisions

- The app is intentionally small: FastAPI, local files, and numpy vector search are enough for a reviewable prototype.
- The OpenAI layer is optional because reviewers should be able to run the submission without a secret key.
- The local fallback includes query expansion for common fashion intents like beach, summer, running, office, wedding, winter, and travel.
- The recommender rejects non-fashion requests before vector search because nearest-neighbor search will otherwise always return something, even for unrelated questions. The guard still allows compact product-attribute searches such as color and pattern terms.
- Audience filtering keeps mens, womens, unisex, and kids-oriented matches aligned with the request instead of relying on similarity alone.
- `categories` are not used as a primary signal because the inspected Amazon Fashion file has empty category arrays for the sampled rows.
- The vector index is file-based for simplicity. A production version would move embeddings into a vector database and add background indexing.

## Data Notes

The Amazon Fashion metadata contains 826,108 rows. Many rows have title, store, rating, image, and product-detail fields; fewer rows have price and long descriptions. The ingestion code therefore builds product text from title, features, description, store, and selected detail fields. Missing prices are expected in the source data, so the UI includes a "Listed price only" option and the API exposes `filters.require_price`.

## Tests

```powershell
.\.venv\Scripts\pytest
```
