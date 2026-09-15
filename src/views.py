from __future__ import annotations

from datetime import date

from .models import STAGES, TIERS, Listing

_TIER_ORDER = {tier: i for i, tier in enumerate(TIERS)}


def days_in_stage(listing: Listing, today: date) -> int:
    """`history[-1].occurred` is the clock — see ARCHITECTURE.md §5.2 / §6.1."""
    if not listing.history:
        raise ValueError(f"{listing.id} has no history — every listing on the board must have one")
    return (today - listing.history[-1].occurred).days


def interview_board(
    listings: list[Listing], today: date | None = None
) -> dict[str, list[Listing]]:
    """Columns, oldest first within each — the only sort (ARCHITECTURE.md §5.6)."""
    today = today or date.today()
    columns: dict[str, list[Listing]] = {stage: [] for stage in STAGES}
    for listing in listings:
        assert listing.stage is not None, f"{listing.id} has no stage — queued, not on the board"
        columns.setdefault(listing.stage, []).append(listing)
    for stage_listings in columns.values():
        stage_listings.sort(key=lambda c: (-days_in_stage(c, today), c.company))
    return columns


def queue(listings: list[Listing]) -> list[Listing]:
    """The Job Listings queue, sorted by tier then comp (ARCHITECTURE.md §6.2)."""

    def comp_key(listing: Listing) -> int:
        return -(listing.comp.max or listing.comp.min or 0)

    def tier_key(listing: Listing) -> int:
        tier = listing.assessment.tier
        return len(TIERS) if tier is None else _TIER_ORDER.get(tier, len(TIERS))

    return sorted(listings, key=lambda c: (tier_key(c), comp_key(c)))
