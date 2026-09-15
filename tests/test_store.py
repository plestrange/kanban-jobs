import shutil
from pathlib import Path

import pytest

import src.store as store

FIXTURES = Path("tests/fixtures")


@pytest.fixture()
def root(tmp_path):
    dest = tmp_path / "data"
    shutil.copytree(FIXTURES, dest)
    return dest


def test_load_interview_board_and_listings(root):
    board = store.load_interview_board(root=root)
    listings = store.load_listings(root=root)
    assert {c.id for c in board} == {"acme-sr-mlops", "globex-mle", "initech-platform"}
    assert {c.id for c in listings} == {"umbrella-mlops", "hooli-ml-eng"}


def test_company_summary_defaults_to_empty_string(root):
    acme = next(c for c in store.load_interview_board(root=root) if c.id == "acme-sr-mlops")
    globex = next(c for c in store.load_interview_board(root=root) if c.id == "globex-mle")
    assert acme.company_summary == "Industrial robotics company."
    assert globex.company_summary == ""  # fixture predates the field


def test_load_finds_listing_in_either_dir(root):
    assert store.load("acme-sr-mlops", root=root).company == "Acme Robotics"
    assert store.load("umbrella-mlops", root=root).company == "Umbrella Analytics"


def test_load_missing_raises(root):
    with pytest.raises(FileNotFoundError):
        store.load("does-not-exist", root=root)


def test_save_is_atomic_and_roundtrips(root):
    listing = store.load("acme-sr-mlops", root=root)
    path = root / "interview-board" / "acme-sr-mlops.yaml"
    mtime = path.stat().st_mtime
    listing.notes = "updated during test"

    store.save(listing, mtime, root=root)

    reloaded = store.load("acme-sr-mlops", root=root)
    assert reloaded.notes == "updated during test"
    assert not list(path.parent.glob("*.tmp"))  # no leftover temp file


def test_save_raises_conflict_on_stale_mtime(root):
    listing = store.load("acme-sr-mlops", root=root)
    path = root / "interview-board" / "acme-sr-mlops.yaml"
    stale_mtime = path.stat().st_mtime

    other = store.load("acme-sr-mlops", root=root)
    other.notes = "changed elsewhere first"
    store.save(other, stale_mtime, root=root)

    listing.notes = "conflicting change"
    with pytest.raises(store.ConflictError):
        store.save(listing, stale_mtime, root=root)


def test_review_interested_moves_to_shortlist(root):
    listing = store.review("umbrella-mlops", interested=True, root=root)
    assert listing.stage == "shortlist"
    assert not (root / "listings" / "umbrella-mlops.yaml").exists()
    assert (root / "interview-board" / "umbrella-mlops.yaml").exists()
    assert len(listing.history) == 1


def test_review_pass_archives_with_reason(root):
    listing = store.review("hooli-ml-eng", interested=False, root=root)
    assert listing.stage == "archived"
    assert listing.reason == "passed"
    assert not (root / "listings" / "hooli-ml-eng.yaml").exists()
