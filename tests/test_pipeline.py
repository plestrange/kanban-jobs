from datetime import date
from pathlib import Path

import pytest

from src.pipeline import amend, complete, move, round_done, uncomplete
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


def test_complete_marks_round_done_without_changing_stage():
    listing = _acme()
    n = len(listing.history)
    complete(listing, note="onsite", occurred=date(2026, 9, 2))
    assert listing.stage == "technical"
    assert round_done(listing)
    assert len(listing.history) == n + 1
    assert listing.history[-1].to == "technical"
    assert listing.history[-1].completed
    assert listing.history[-1].occurred == date(2026, 9, 2)


def test_move_after_complete_clears_done():
    listing = _acme()
    complete(listing)
    move(listing, "panel")
    assert not round_done(listing)


def test_complete_rejects_non_round_stage():
    listing = _acme()
    move(listing, "applied")
    with pytest.raises(ValueError):
        complete(listing)


def test_complete_rejects_already_done():
    listing = _acme()
    complete(listing)
    with pytest.raises(ValueError):
        complete(listing)


def test_complete_rejects_future_occurred():
    listing = _acme()
    with pytest.raises(ValueError):
        complete(listing, occurred=date(2999, 1, 1))


def test_uncomplete_removes_the_completed_entry():
    listing = _acme()
    before = list(listing.history)
    complete(listing)
    uncomplete(listing)
    assert listing.history == before
    assert not round_done(listing)


def test_uncomplete_rejects_when_not_done():
    listing = _acme()
    with pytest.raises(ValueError):
        uncomplete(listing)
