from datetime import date
from pathlib import Path

import pytest

from core.pipeline import amend, move
from core.store import load_cards

FIXTURES = Path("tests/fixtures")


def _acme():
    return next(c for c in load_cards(root=FIXTURES) if c.id == "acme-sr-mlops")


def test_move_appends_history_and_sets_stage():
    card = _acme()
    n = len(card.history)
    move(card, "take-home", occurred=date(2026, 9, 1))
    assert card.stage == "take-home"
    assert len(card.history) == n + 1
    assert card.history[-1].to == "take-home"
    assert card.history[-1].occurred == date(2026, 9, 1)


def test_move_to_archived_sets_reason_and_clears_on_move_away():
    card = _acme()
    move(card, "archived", reason="withdrew")
    assert card.stage == "archived"
    assert card.reason == "withdrew"

    move(card, "shortlist")
    assert card.reason is None


def test_move_rejects_future_occurred():
    card = _acme()
    with pytest.raises(ValueError):
        move(card, "panel", occurred=date(2999, 1, 1))


def test_move_any_stage_to_any_stage():
    card = _acme()
    move(card, "offer")
    assert card.stage == "offer"


def test_amend_corrects_occurred_and_note():
    card = _acme()
    idx = len(card.history) - 1
    original_recorded = card.history[idx].recorded
    amend(card, idx, occurred=date(2026, 8, 26), note="corrected date")
    assert card.history[idx].occurred == date(2026, 8, 26)
    assert card.history[idx].note == "corrected date"
    assert card.history[idx].recorded == original_recorded  # never editable


def test_amend_rejects_occurred_after_recorded():
    card = _acme()
    idx = len(card.history) - 1
    with pytest.raises(ValueError):
        amend(card, idx, occurred=date(2999, 1, 1))
