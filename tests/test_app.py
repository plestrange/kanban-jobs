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


def test_index_redirects_to_board(client):
    res = client.get("/")
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/board")


def test_board_groups_cards_by_stage(client):
    res = client.get("/board")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "Acme Robotics" in body  # stage: technical
    assert "Globex Corporation" in body  # stage: applied
    assert "Initech" in body  # stage: archived, shown in the collapsed lane


def test_board_shows_archive_note(client):
    res = client.get("/board")
    body = res.get_data(as_text=True)
    assert "rejected after recruiter screen" in body


def test_board_shows_days_in_stage(client):
    res = client.get("/board")
    body = res.get_data(as_text=True)
    assert "days</span>" in body


def test_board_links_to_posting(client):
    res = client.get("/board")
    body = res.get_data(as_text=True)
    assert 'href="https://job-boards.greenhouse.io/acme/jobs/9001234567"' in body


def test_discovery_page_lists_inbox_cards(client):
    res = client.get("/discovery")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "Umbrella Analytics" in body
    assert "Hooli" in body
    assert "Data-broker risk analytics platform." in body


def test_api_inbox_sorted_by_tier_then_comp(client):
    res = client.get("/api/inbox")
    assert res.status_code == 200
    cards = res.get_json()
    assert [c["id"] for c in cards] == ["umbrella-mlops", "hooli-ml-eng"]
    assert cards[0]["company_summary"] == "Data-broker risk analytics platform."
    assert cards[1]["company_summary"] == ""  # fixture predates the field


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


def _mtime(client, card_id):
    res = client.get("/board")
    body = res.get_data(as_text=True)
    marker = f'data-id="{card_id}"'
    idx = body.index(marker)
    attr = 'data-mtime="'
    start = body.index(attr, idx) + len(attr)
    end = body.index('"', start)
    return float(body[start:end])


def test_move_stage_updates_card(client):
    mtime = _mtime(client, "globex-mle")
    res = client.patch(
        "/api/cards/globex-mle/stage", json={"to": "informational", "mtime": mtime}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["stage"] == "informational"
    assert "mtime" in data


def test_move_stage_to_archived_requires_reason(client):
    mtime = _mtime(client, "globex-mle")
    res = client.patch("/api/cards/globex-mle/stage", json={"to": "archived", "mtime": mtime})
    assert res.status_code == 400


def test_move_stage_to_archived_with_reason(client):
    mtime = _mtime(client, "globex-mle")
    res = client.patch(
        "/api/cards/globex-mle/stage",
        json={"to": "archived", "reason": "withdrew", "note": "took another offer", "mtime": mtime},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["stage"] == "archived"
    assert data["reason"] == "withdrew"
    assert data["note"] == "took another offer"


def test_move_stage_conflict_on_stale_mtime(client):
    res = client.patch(
        "/api/cards/globex-mle/stage", json={"to": "informational", "mtime": 1.0}
    )
    assert res.status_code == 409
    assert res.get_json()["error"] == "conflict"


def test_move_stage_unknown_card_404s(client):
    res = client.patch(
        "/api/cards/does-not-exist/stage", json={"to": "applied", "mtime": 1.0}
    )
    assert res.status_code == 404


def test_move_stage_invalid_target_400s(client):
    mtime = _mtime(client, "globex-mle")
    res = client.patch(
        "/api/cards/globex-mle/stage", json={"to": "not-a-stage", "mtime": mtime}
    )
    assert res.status_code == 400


def test_board_renders_draggable_cards_with_mtime(client):
    res = client.get("/board")
    body = res.get_data(as_text=True)
    assert 'draggable="true"' in body
    assert 'data-stage="applied"' in body
