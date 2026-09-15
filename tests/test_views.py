from datetime import date
from pathlib import Path

from src.models import Assessment, Comp, Discovered, HistoryEntry, Listing, Location
from src.store import load_interview_board, load_listings
from src.views import days_in_stage, interview_board, queue

FIXTURES = Path("tests/fixtures")


def _listings():
    return load_interview_board(root=FIXTURES)


def _listing(id_, company, stage, occurred):
    return Listing(
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
    listing = next(c for c in _listings() if c.id == "acme-sr-mlops")
    assert days_in_stage(listing, date(2026, 9, 4)) == 8  # entered technical 2026-08-27


def test_interview_board_groups_by_stage():
    columns = interview_board(_listings(), today=date(2026, 9, 10))
    assert [c.id for c in columns["technical"]] == ["acme-sr-mlops"]
    assert [c.id for c in columns["applied"]] == ["globex-mle"]
    assert [c.id for c in columns["archived"]] == ["initech-platform"]
    assert columns["offer"] == []


def test_interview_board_sorts_oldest_first_within_a_column():
    listings = [
        _listing("newer", "Beta Co", "applied", date(2026, 9, 5)),
        _listing("older", "Alpha Co", "applied", date(2026, 8, 1)),
        _listing("tie-b", "Zeta Co", "applied", date(2026, 9, 1)),
        _listing("tie-a", "Alpha Co", "applied", date(2026, 9, 1)),
    ]
    columns = interview_board(listings, today=date(2026, 9, 10))
    assert [c.id for c in columns["applied"]] == ["older", "tie-a", "tie-b", "newer"]


def test_queue_sorts_by_tier_then_comp():
    ordered = queue(load_listings(root=FIXTURES))
    assert [c.id for c in ordered] == ["umbrella-mlops", "hooli-ml-eng"]
