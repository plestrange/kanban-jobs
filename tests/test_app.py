import shutil
from pathlib import Path

import pytest

from app.server import create_app

FIXTURES = Path("tests/fixtures")


@pytest.fixture()
def client(tmp_path):
    root = tmp_path / "data"
    shutil.copytree(FIXTURES, root)
    app = create_app(root=root)
    app.config["TESTING"] = True
    return app.test_client()


def test_index_redirects_to_discovery(client):
    res = client.get("/")
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/discovery")


def test_discovery_page_lists_inbox_cards(client):
    res = client.get("/discovery")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "Umbrella Analytics" in body
    assert "Hooli" in body


def test_api_inbox_sorted_by_tier_then_comp(client):
    res = client.get("/api/inbox")
    assert res.status_code == 200
    ids = [c["id"] for c in res.get_json()]
    assert ids == ["umbrella-mlops", "hooli-ml-eng"]


def test_review_interested_removes_from_inbox(client, tmp_path):
    res = client.post("/api/inbox/umbrella-mlops/review", json={"interested": True})
    assert res.status_code == 200
    assert res.get_json()["stage"] == "shortlist"
    assert [c["id"] for c in client.get("/api/inbox").get_json()] == ["hooli-ml-eng"]


def test_review_pass_with_note_archives(client):
    res = client.post(
        "/api/inbox/hooli-ml-eng/review", json={"interested": False, "note": "not a fit right now"}
    )
    assert res.status_code == 200
    assert res.get_json()["stage"] == "archived"


def test_review_unknown_card_404s(client):
    res = client.post("/api/inbox/does-not-exist/review", json={"interested": True})
    assert res.status_code == 404
