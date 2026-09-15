"""The two-writer rule (docs/design/ARCHITECTURE.md §4, §9): a job search sweep writes only
listings/, the app writes only interview-board/. This is a convention, not a mechanism
(§12) — these tests are the mechanism that catches drift.
"""

import hashlib
import shutil
from pathlib import Path

import pytest
import yaml

import src.store as store

FIXTURES = Path("tests/fixtures")


@pytest.fixture()
def root(tmp_path):
    dest = tmp_path / "data"
    shutil.copytree(FIXTURES, dest)
    return dest


def _hash_tree(dir_path: Path) -> dict[str, str]:
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(dir_path.glob("*.yaml"))
    }


def test_reads_never_mutate_disk(root):
    before_board = _hash_tree(root / "interview-board")
    before_listings = _hash_tree(root / "listings")

    store.load_interview_board(root=root)
    store.load_listings(root=root)
    store.load("acme-sr-mlops", root=root)

    assert _hash_tree(root / "interview-board") == before_board
    assert _hash_tree(root / "listings") == before_listings


def test_simulated_search_sweep_never_touches_interview_board(root):
    """A job search sweep is a Claude session writing YAML files directly —
    it never calls src.store at all. Simulate that and assert interview-board/ is inert.
    """
    before_board = _hash_tree(root / "interview-board")

    new_candidate = {
        "id": "wonka-mle",
        "req_id": "wk-1",
        "company": "Wonka Analytics",
        "title": "ML Engineer",
        "team": None,
        "location": {"mode": "remote", "scope": "US", "eligible": True},
        "comp": {"min": 150000, "max": 190000, "currency": "USD", "source": "posted"},
        "url": "https://jobs.lever.co/wonka/wk-1",
        "url_kind": "ats",
        "discovered": {"date": "2026-09-10", "via": "test sweep", "rubric": "v1"},
        "assessment": {"tier": "good", "why": "test", "gap": "test"},
    }
    (root / "listings" / "wonka-mle.yaml").write_text(yaml.safe_dump(new_candidate))

    assert _hash_tree(root / "interview-board") == before_board
    assert "wonka-mle.yaml" in _hash_tree(root / "listings")


def test_review_is_the_only_seam_from_listings_to_interview_board(root):
    """review() is the one function that reads listings/ and writes interview-board/.
    Confirm it removes the listings copy so no listing ever exists in both places at once.
    """
    store.review("hooli-ml-eng", interested=True, root=root)
    assert not (root / "listings" / "hooli-ml-eng.yaml").exists()
    assert (root / "interview-board" / "hooli-ml-eng.yaml").exists()
