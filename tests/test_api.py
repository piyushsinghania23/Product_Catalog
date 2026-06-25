import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app, initialize_database, seed_products


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "products.db"
    monkeypatch.setenv("PRODUCTS_DB_PATH", str(db_path))
    initialize_database()
    seed_products(250, db_path=str(db_path))
    with TestClient(app) as client:
        yield client


def test_products_endpoint_returns_newest_first_and_paginates(client):
    first_page = client.get("/products", params={"limit": 10}).json()

    assert first_page["count"] == 10
    assert first_page["has_more"] is True
    assert first_page["next_cursor"] is not None

    items = first_page["items"]
    assert items == sorted(items, key=lambda item: (item["updated_at"], item["id"]), reverse=True)

    second_page = client.get("/products", params={"limit": 10, "cursor": first_page["next_cursor"]}).json()
    assert second_page["count"] == 10

    seen_ids = [item["id"] for item in items] + [item["id"] for item in second_page["items"]]
    assert len(seen_ids) == len(set(seen_ids))


def test_cursor_pagination_stays_stable_when_new_products_arrive(client):
    first_page = client.get("/products", params={"limit": 5}).json()
    first_ids = [item["id"] for item in first_page["items"]]

    seed_products(10, db_path=os.environ["PRODUCTS_DB_PATH"], prefix="fresh")

    second_page = client.get("/products", params={"limit": 5, "cursor": first_page["next_cursor"]}).json()
    second_ids = [item["id"] for item in second_page["items"]]

    assert len(first_ids) + len(second_ids) == len(set(first_ids + second_ids))
    assert set(first_ids).isdisjoint(set(second_ids))
