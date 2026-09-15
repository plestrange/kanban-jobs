from datetime import date
from pathlib import Path

import pytest

from src.pipeline import amend, move
from src.store import load_interview_board

FIXTURES = Path("tests/fixtures")


def _acme():
    return next(c for c in load_interview_board(root=FIXTURES) if c.id == "acme-sr-mlops")


def test_move_appends_history_and_sets_stage():
    listing = _acme()
    n = len(listing.history)
    move(listing, "take-home", occurred=date(2026, 9, 1))
    assert listing.stage == "take-home"
    assert len(listing.history) == n + 1
    assert listing.history[-1].to == "take-home"
    assert listing.history[-1].occurred == date(2026, 9, 1)


def test_move_to_archived_sets_reason_and_clears_on_move_away():
    listing = _acme()
    move(listing, "archived", reason="withdrew")
    assert listing.stage == "archived"
    assert listing.reason == "withdrew"

    move(listing, "shortlist")
    assert listing.reason is None


def test_move_rejects_future_occurred():
    listing = _acme()
    with pytest.raises(ValueError):
        move(listing, "panel", occurred=date(2999, 1, 1))


def test_move_any_stage_to_any_stage():
    listing = _acme()
    move(listing, "offer")
    assert listing.stage == "offer"


def test_amend_corrects_occurred_and_note():
    listing = _acme()
    idx = len(listing.history) - 1
    original_recorded = listing.history[idx].recorded
    amend(listing, idx, occurred=date(2026, 8, 26), note="corrected date")
    assert listing.history[idx].occurred == date(2026, 8, 26)
    assert listing.history[idx].note == "corrected date"
    assert listing.history[idx].recorded == original_recorded  # never editable


def test_amend_rejects_occurred_after_recorded():
    listing = _acme()
    idx = len(listing.history) - 1
    with pytest.raises(ValueError):
        amend(listing, idx, occurred=date(2999, 1, 1))
