# Fast Product Catalog

A small FastAPI backend for browsing products with cursor-based pagination and category filtering.

## Features
- Fast pagination over a large SQLite-backed product catalog
- Category filtering
- Stable cursor pagination that avoids duplicates or skips when new rows arrive
- Seed script for generating 200,000 products efficiently

## Run locally
1. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
2. Initialize the database and seed products:
   ```bash
   python seed_products.py --count 200000 --reset
   ```
3. Start the API:
   ```bash
   uvicorn app.main:app --reload
   ```

## Example requests
- List products:
  ```bash
  curl "http://127.0.0.1:8000/products?limit=20"
  ```
- Filter by category:
  ```bash
  curl "http://127.0.0.1:8000/products?category=electronics&limit=20"
  ```

## Why this approach
- SQLite is sufficient for this task size and keeps deployment simple.
- Cursor pagination is used instead of offset pagination because offset pagination becomes slow and unstable on large datasets.
- The cursor uses the latest ordering key and product id to provide a consistent and efficient paging experience.
