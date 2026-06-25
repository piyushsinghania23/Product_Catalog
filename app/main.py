import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Fast Product Catalog")


def get_db_path() -> str:
    return os.getenv("PRODUCTS_DB_PATH", str(Path(__file__).resolve().parent.parent / "products.db"))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def initialize_database() -> None:
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_products_updated_id ON products(updated_at DESC, id DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_products_category_updated_id ON products(category, updated_at DESC, id DESC)")
    conn.commit()
    conn.close()


def seed_products(count: int = 200_000, db_path: str | None = None, prefix: str = "product", reset: bool = False) -> None:
    target_db = db_path or get_db_path()
    conn = sqlite3.connect(target_db)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    if reset:
        conn.execute("DELETE FROM products")

    categories = ["electronics", "clothing", "books", "home", "sports"]
    batch_size = 5000
    existing_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    for start in range(0, count, batch_size):
        end = min(start + batch_size, count)
        rows = []
        for i in range(start, end):
            product_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).isoformat(timespec="microseconds")
            rows.append(
                (
                    product_id,
                    f"{prefix}-{existing_count + i + 1}",
                    categories[(existing_count + i) % len(categories)],
                    round(10 + ((existing_count + i) % 1000) + ((existing_count + i) % 11) * 0.5, 2),
                    timestamp,
                    timestamp,
                )
            )
        conn.executemany(
            """
            INSERT INTO products (id, name, category, price, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

    conn.commit()
    conn.close()


class ProductOut(BaseModel):
    id: str
    name: str
    category: str
    price: float
    created_at: str
    updated_at: str


@app.get("/")
def index() -> FileResponse:
    return FileResponse(Path(__file__).resolve().parent / "static" / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/products", response_model=dict[str, Any])
def list_products(
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    conn = get_connection()
    query = "SELECT id, name, category, price, created_at, updated_at FROM products"
    params: list[Any] = []
    where_clauses: list[str] = []

    if category:
        where_clauses.append("category = ?")
        params.append(category)

    if cursor:
        where_clauses.append("(updated_at, id) < (?, ?)")
        params.extend(cursor.split("|", 1))

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " ORDER BY updated_at DESC, id DESC LIMIT ?"
    params.append(limit + 1)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    items = [dict(row) for row in rows[:limit]]
    has_more = len(rows) > limit
    next_cursor = None
    if has_more and items:
        last_item = items[-1]
        next_cursor = f"{last_item['updated_at']}|{last_item['id']}"

    return {"items": items, "count": len(items), "has_more": has_more, "next_cursor": next_cursor}
