from __future__ import annotations

from datetime import date

from .models import STAGES, TIERS, Card

_TIER_ORDER = {tier: i for i, tier in enumerate(TIERS)}


def days_in_stage(card: Card, today: date) -> int:
    """`history[-1].occurred` is the clock — see ARCHITECTURE.md §5.2 / §6.1."""
    if not card.history:
        raise ValueError(f"{card.id} has no history — every card in cards/ must have one")
    return (today - card.history[-1].occurred).days


def board(cards: list[Card], today: date | None = None) -> dict[str, list[Card]]:
    """Columns, oldest first within each — the only sort (ARCHITECTURE.md §5.6)."""
    today = today or date.today()
    columns: dict[str, list[Card]] = {stage: [] for stage in STAGES}
    for card in cards:
        columns.setdefault(card.stage, []).append(card)
    for stage_cards in columns.values():
        stage_cards.sort(key=lambda c: (-days_in_stage(c, today), c.company))
    return columns


def queue(cards: list[Card]) -> list[Card]:
    """Inbox, sorted by tier then comp (ARCHITECTURE.md §6.2)."""

    def comp_key(card: Card) -> int:
        return -(card.comp.max or card.comp.min or 0)

    return sorted(cards, key=lambda c: (_TIER_ORDER.get(c.assessment.tier, len(TIERS)), comp_key(c)))
