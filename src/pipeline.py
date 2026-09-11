from __future__ import annotations

from datetime import date

from .models import Card, HistoryEntry


def move(
    card: Card,
    to_stage: str,
    reason: str | None = None,
    note: str = "",
    occurred: date | None = None,
) -> Card:
    """The only place stage changes. Appends to history and rewrites `stage`.

    Any stage moves to any stage — there is no transition table (docs/ARCHITECTURE.md §6.1).
    """
    recorded = date.today()
    occurred = occurred or recorded
    if occurred > recorded:
        raise ValueError("occurred cannot be later than recorded — backdate, don't forward-date")

    card.history.append(HistoryEntry(occurred=occurred, recorded=recorded, to=to_stage, note=note))
    card.stage = to_stage
    card.reason = reason if to_stage == "archived" else None
    return card


def amend(card: Card, index: int, occurred: date | None = None, note: str | None = None) -> Card:
    """Correct a past history entry. `recorded` is never editable (docs/ARCHITECTURE.md §5.2)."""
    entry = card.history[index]
    if occurred is not None:
        if occurred > entry.recorded:
            raise ValueError("occurred cannot be later than recorded")
        entry.occurred = occurred
    if note is not None:
        entry.note = note
    return card
