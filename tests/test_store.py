import shutil
from pathlib import Path

import pytest

import core.store as store

FIXTURES = Path("tests/fixtures")


@pytest.fixture()
def root(tmp_path):
    dest = tmp_path / "data"
    shutil.copytree(FIXTURES, dest)
    return dest


def test_load_cards_and_inbox(root):
    cards = store.load_cards(root=root)
    inbox = store.load_inbox(root=root)
    assert {c.id for c in cards} == {"acme-sr-mlops", "globex-mle", "initech-platform"}
    assert {c.id for c in inbox} == {"umbrella-mlops", "hooli-ml-eng"}


def test_load_finds_card_in_either_dir(root):
    assert store.load("acme-sr-mlops", root=root).company == "Acme Robotics"
    assert store.load("umbrella-mlops", root=root).company == "Umbrella Analytics"


def test_load_missing_raises(root):
    with pytest.raises(FileNotFoundError):
        store.load("does-not-exist", root=root)


def test_save_is_atomic_and_roundtrips(root):
    card = store.load("acme-sr-mlops", root=root)
    path = root / "cards" / "acme-sr-mlops.yaml"
    mtime = path.stat().st_mtime
    card.notes = "updated during test"

    store.save(card, mtime, root=root)

    reloaded = store.load("acme-sr-mlops", root=root)
    assert reloaded.notes == "updated during test"
    assert not list(path.parent.glob("*.tmp"))  # no leftover temp file


def test_save_raises_conflict_on_stale_mtime(root):
    card = store.load("acme-sr-mlops", root=root)
    path = root / "cards" / "acme-sr-mlops.yaml"
    stale_mtime = path.stat().st_mtime

    other = store.load("acme-sr-mlops", root=root)
    other.notes = "changed elsewhere first"
    store.save(other, stale_mtime, root=root)

    card.notes = "conflicting change"
    with pytest.raises(store.ConflictError):
        store.save(card, stale_mtime, root=root)


def test_review_interested_moves_to_shortlist(root):
    card = store.review("umbrella-mlops", interested=True, root=root)
    assert card.stage == "shortlist"
    assert not (root / "inbox" / "umbrella-mlops.yaml").exists()
    assert (root / "cards" / "umbrella-mlops.yaml").exists()
    assert len(card.history) == 1


def test_review_pass_archives_with_reason(root):
    card = store.review("hooli-ml-eng", interested=False, root=root)
    assert card.stage == "archived"
    assert card.reason == "passed"
    assert not (root / "inbox" / "hooli-ml-eng.yaml").exists()
