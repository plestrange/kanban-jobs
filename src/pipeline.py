from __future__ import annotations

from datetime import date

from .models import HistoryEntry, Listing


def move(
    listing: Listing,
    to_stage: str,
    reason: str | None = None,
    note: str = "",
    occurred: date | None = None,
) -> Listing:
    """The only place stage changes. Appends to history and rewrites `stage`.

    Any stage moves to any stage — there is no transition table (ARCHITECTURE.md §6.1).
    """
    recorded = date.today()
    occurred = occurred or recorded
    if occurred > recorded:
        raise ValueError("occurred cannot be later than recorded — backdate, don't forward-date")

    listing.history.append(
        HistoryEntry(occurred=occurred, recorded=recorded, to=to_stage, note=note)
    )
    listing.stage = to_stage
    listing.reason = reason if to_stage == "archived" else None
    return listing


def amend(
    listing: Listing, index: int, occurred: date | None = None, note: str | None = None
) -> Listing:
    """Correct a past history entry. `recorded` is never editable (ARCHITECTURE.md §5.2)."""
    entry = listing.history[index]
    if occurred is not None:
        if occurred > entry.recorded:
            raise ValueError("occurred cannot be later than recorded")
        entry.occurred = occurred
    if note is not None:
        entry.note = note
    return listing
