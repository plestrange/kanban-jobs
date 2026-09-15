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


def test_index_redirects_to_interview_board(client):
    res = client.get("/")
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/interview-board")


def test_interview_board_groups_listings_by_stage(client):
    res = client.get("/interview-board")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "Acme Robotics" in body  # stage: technical
    assert "Globex Corporation" in body  # stage: applied
    assert "Initech" in body  # stage: archived, shown in the collapsed lane


def test_interview_board_shows_archive_note(client):
    res = client.get("/interview-board")
    body = res.get_data(as_text=True)
    assert "rejected after recruiter screen" in body


def test_interview_board_shows_days_in_stage(client):
    res = client.get("/interview-board")
    body = res.get_data(as_text=True)
    assert "days</span>" in body


def test_interview_board_links_to_posting(client):
    res = client.get("/interview-board")
    body = res.get_data(as_text=True)
    assert 'href="https://job-boards.greenhouse.io/acme/jobs/9001234567"' in body


def test_listings_page_lists_queued_listings(client):
    res = client.get("/listings")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "Umbrella Analytics" in body
    assert "Hooli" in body
    assert "Data-broker risk analytics platform." in body


def test_api_listings_sorted_by_tier_then_comp(client):
    res = client.get("/api/listings")
    assert res.status_code == 200
    listings = res.get_json()
    assert [c["id"] for c in listings] == ["umbrella-mlops", "hooli-ml-eng"]
    assert listings[0]["company_summary"] == "Data-broker risk analytics platform."
    assert listings[1]["company_summary"] == ""  # fixture predates the field


def test_review_interested_removes_from_listings(client, tmp_path):
    res = client.post("/api/listings/umbrella-mlops/review", json={"interested": True})
    assert res.status_code == 200
    assert res.get_json()["stage"] == "shortlist"
    assert [c["id"] for c in client.get("/api/listings").get_json()] == ["hooli-ml-eng"]


def test_review_pass_with_note_archives(client):
    res = client.post(
        "/api/listings/hooli-ml-eng/review",
        json={"interested": False, "note": "not a fit right now"},
    )
    assert res.status_code == 200
    assert res.get_json()["stage"] == "archived"


def test_review_unknown_listing_404s(client):
    res = client.post("/api/listings/does-not-exist/review", json={"interested": True})
    assert res.status_code == 404


def _mtime(client, listing_id):
    res = client.get("/interview-board")
    body = res.get_data(as_text=True)
    marker = f'data-id="{listing_id}"'
    idx = body.index(marker)
    attr = 'data-mtime="'
    start = body.index(attr, idx) + len(attr)
    end = body.index('"', start)
    return float(body[start:end])


def test_move_stage_updates_listing(client):
    mtime = _mtime(client, "globex-mle")
    res = client.patch(
        "/api/interview-board/globex-mle/stage", json={"to": "informational", "mtime": mtime}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["stage"] == "informational"
    assert "mtime" in data


def test_move_stage_to_archived_requires_reason(client):
    mtime = _mtime(client, "globex-mle")
    res = client.patch(
        "/api/interview-board/globex-mle/stage", json={"to": "archived", "mtime": mtime}
    )
    assert res.status_code == 400


def test_move_stage_to_archived_with_reason(client):
    mtime = _mtime(client, "globex-mle")
    res = client.patch(
        "/api/interview-board/globex-mle/stage",
        json={"to": "archived", "reason": "withdrew", "note": "took another offer", "mtime": mtime},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["stage"] == "archived"
    assert data["reason"] == "withdrew"
    assert data["note"] == "took another offer"


def test_move_stage_conflict_on_stale_mtime(client):
    res = client.patch(
        "/api/interview-board/globex-mle/stage", json={"to": "informational", "mtime": 1.0}
    )
    assert res.status_code == 409
    assert res.get_json()["error"] == "conflict"


def test_move_stage_unknown_listing_404s(client):
    res = client.patch(
        "/api/interview-board/does-not-exist/stage", json={"to": "applied", "mtime": 1.0}
    )
    assert res.status_code == 404


def test_move_stage_invalid_target_400s(client):
    mtime = _mtime(client, "globex-mle")
    res = client.patch(
        "/api/interview-board/globex-mle/stage", json={"to": "not-a-stage", "mtime": mtime}
    )
    assert res.status_code == 400


def test_interview_board_renders_draggable_listings_with_mtime(client):
    res = client.get("/interview-board")
    body = res.get_data(as_text=True)
    assert 'draggable="true"' in body
    assert 'data-stage="applied"' in body


def test_listing_detail_renders(client):
    res = client.get("/interview-board/acme-sr-mlops")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "Acme Robotics" in body
    assert "Jordan Rivas" in body
    assert "review staged-rollout design" in body


def test_listing_detail_unknown_404s(client):
    res = client.get("/interview-board/does-not-exist")
    assert res.status_code == 404


def test_update_listing_notes(client):
    mtime = _mtime(client, "acme-sr-mlops")
    res = client.patch(
        "/api/interview-board/acme-sr-mlops", json={"notes": "new prep notes", "mtime": mtime}
    )
    assert res.status_code == 200
    assert res.get_json()["notes"] == "new prep notes"


def test_update_listing_referral(client):
    mtime = _mtime(client, "acme-sr-mlops")
    res = client.patch(
        "/api/interview-board/acme-sr-mlops",
        json={
            "referral": {"status": "possible", "via": "a friend", "checked": "2026-09-10"},
            "mtime": mtime,
        },
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["referral"] == {"status": "possible", "via": "a friend", "checked": "2026-09-10"}


def test_update_listing_referral_invalid_status_400s(client):
    mtime = _mtime(client, "acme-sr-mlops")
    res = client.patch(
        "/api/interview-board/acme-sr-mlops",
        json={"referral": {"status": "nope"}, "mtime": mtime},
    )
    assert res.status_code == 400


def test_update_listing_contacts_replaces_list_and_drops_blank_names(client):
    mtime = _mtime(client, "acme-sr-mlops")
    res = client.patch(
        "/api/interview-board/acme-sr-mlops",
        json={
            "contacts": [
                {"name": "Dana Lee", "role": "hiring manager", "note": ""},
                {"name": "", "role": "should be dropped"},
            ],
            "mtime": mtime,
        },
    )
    assert res.status_code == 200
    assert res.get_json()["contacts"] == [
        {"name": "Dana Lee", "role": "hiring manager", "note": ""}
    ]


def test_update_listing_conflict_on_stale_mtime(client):
    res = client.patch("/api/interview-board/acme-sr-mlops", json={"notes": "x", "mtime": 1.0})
    assert res.status_code == 409
    assert res.get_json()["error"] == "conflict"


def test_amend_history_entry_updates_occurred_and_note(client):
    mtime = _mtime(client, "acme-sr-mlops")
    res = client.patch(
        "/api/interview-board/acme-sr-mlops/history/1",
        json={
            "occurred": "2026-08-13",
            "note": "applied a day earlier than logged",
            "mtime": mtime,
        },
    )
    assert res.status_code == 200
    entry = res.get_json()["history"][1]
    assert entry["occurred"] == "2026-08-13"
    assert entry["note"] == "applied a day earlier than logged"
    assert entry["recorded"] == "2026-08-14"  # unchanged


def test_amend_history_future_occurred_400s(client):
    mtime = _mtime(client, "acme-sr-mlops")
    res = client.patch(
        "/api/interview-board/acme-sr-mlops/history/1",
        json={"occurred": "2099-01-01", "mtime": mtime},
    )
    assert res.status_code == 400


def test_amend_history_bad_index_404s(client):
    mtime = _mtime(client, "acme-sr-mlops")
    res = client.patch(
        "/api/interview-board/acme-sr-mlops/history/99",
        json={"occurred": "2026-08-13", "mtime": mtime},
    )
    assert res.status_code == 404


def test_amend_history_conflict_on_stale_mtime(client):
    res = client.patch(
        "/api/interview-board/acme-sr-mlops/history/1",
        json={"occurred": "2026-08-13", "mtime": 1.0},
    )
    assert res.status_code == 409
