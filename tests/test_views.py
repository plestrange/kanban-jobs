from datetime import date
from pathlib import Path

from core.models import Assessment, Card, Comp, Discovered, HistoryEntry, Location
from core.store import load_cards, load_inbox
from core.views import board, days_in_stage, queue

FIXTURES = Path("tests/fixtures")


def _cards():
    return load_cards(root=FIXTURES)


def _card(id_, company, stage, occurred):
    return Card(
        id=id_,
        req_id=None,
        company=company,
        title="Engineer",
        team=None,
        location=Location(mode="remote", scope="US"),
        comp=Comp(),
        url="",
        url_kind="ats",
        discovered=Discovered(date=occurred, via="test", rubric="v1"),
        assessment=Assessment(tier="good", why="", gap=""),
        stage=stage,
        history=[HistoryEntry(occurred=occurred, recorded=occurred, to=stage)],
    )


def test_days_in_stage_reads_last_history_entry():
    card = next(c for c in _cards() if c.id == "acme-sr-mlops")
    assert days_in_stage(card, date(2026, 9, 4)) == 8  # entered technical 2026-08-27


def test_board_groups_by_stage():
    columns = board(_cards(), today=date(2026, 9, 10))
    assert [c.id for c in columns["technical"]] == ["acme-sr-mlops"]
    assert [c.id for c in columns["applied"]] == ["globex-mle"]
    assert [c.id for c in columns["archived"]] == ["initech-platform"]
    assert columns["offer"] == []


def test_board_sorts_oldest_first_within_a_column():
    cards = [
        _card("newer", "Beta Co", "applied", date(2026, 9, 5)),
        _card("older", "Alpha Co", "applied", date(2026, 8, 1)),
        _card("tie-b", "Zeta Co", "applied", date(2026, 9, 1)),
        _card("tie-a", "Alpha Co", "applied", date(2026, 9, 1)),
    ]
    columns = board(cards, today=date(2026, 9, 10))
    assert [c.id for c in columns["applied"]] == ["older", "tie-a", "tie-b", "newer"]


def test_queue_sorts_by_tier_then_comp():
    ordered = queue(load_inbox(root=FIXTURES))
    assert [c.id for c in ordered] == ["umbrella-mlops", "hooli-ml-eng"]
