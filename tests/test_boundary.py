"""The two-writer rule (docs/ARCHITECTURE.md §4, §9): discovery writes only inbox/,
the app writes only cards/. This is a convention, not a mechanism (§12) — these
tests are the mechanism that catches drift.
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
    before_cards = _hash_tree(root / "cards")
    before_inbox = _hash_tree(root / "inbox")

    store.load_cards(root=root)
    store.load_inbox(root=root)
    store.load("acme-sr-mlops", root=root)

    assert _hash_tree(root / "cards") == before_cards
    assert _hash_tree(root / "inbox") == before_inbox


def test_simulated_discovery_sweep_never_touches_cards(root):
    """A discovery session is a Claude session writing YAML files directly —
    it never calls src.store at all. Simulate that and assert cards/ is inert.
    """
    before_cards = _hash_tree(root / "cards")

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
    (root / "inbox" / "wonka-mle.yaml").write_text(yaml.safe_dump(new_candidate))

    assert _hash_tree(root / "cards") == before_cards
    assert "wonka-mle.yaml" in _hash_tree(root / "inbox")


def test_review_is_the_only_seam_from_inbox_to_cards(root):
    """review() is the one function that reads inbox/ and writes cards/. Confirm
    it removes the inbox copy so no card ever exists in both places at once.
    """
    store.review("hooli-ml-eng", interested=True, root=root)
    assert not (root / "inbox" / "hooli-ml-eng.yaml").exists()
    assert (root / "cards" / "hooli-ml-eng.yaml").exists()
