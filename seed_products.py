import argparse
import os
from pathlib import Path

from app.main import initialize_database, seed_products


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed a SQLite database with products")
    parser.add_argument("--count", type=int, default=200_000)
    parser.add_argument("--db", type=str, default=None, help="Path to the SQLite database file")
    parser.add_argument("--prefix", type=str, default="product")
    parser.add_argument("--reset", action="store_true", help="Clear existing rows before seeding")
    args = parser.parse_args()

    db_path = args.db or os.getenv("PRODUCTS_DB_PATH", str(Path(__file__).resolve().parent / "products.db"))
    initialize_database()
    seed_products(args.count, db_path=db_path, prefix=args.prefix, reset=args.reset)
    print(f"Seeded {args.count} products into {db_path}")
