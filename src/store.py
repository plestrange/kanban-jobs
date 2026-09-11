from __future__ import annotations

import os
import tempfile
from datetime import date
from pathlib import Path

import yaml

from .config import DATA_DIR
from .models import Card
from .pipeline import move

INBOX = "inbox"
CARDS = "cards"


class ConflictError(Exception):
    """Raised when a save's expected_mtime no longer matches the file on disk."""


def _str_presenter(dumper: yaml.SafeDumper, data: str):
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


yaml.add_representer(str, _str_presenter, Dumper=yaml.SafeDumper)


def _load_dir(dir_path: Path) -> list[Card]:
    if not dir_path.exists():
        return []
    cards = []
    for path in sorted(dir_path.glob("*.yaml")):
        with path.open() as f:
            data = yaml.safe_load(f)
        cards.append(Card.from_dict(data))
    return cards


def load_inbox(root: Path = DATA_DIR) -> list[Card]:
    return _load_dir(root / INBOX)


def load_cards(root: Path = DATA_DIR) -> list[Card]:
    return _load_dir(root / CARDS)


def load(card_id: str, root: Path = DATA_DIR) -> Card:
    for sub in (CARDS, INBOX):
        path = root / sub / f"{card_id}.yaml"
        if path.exists():
            with path.open() as f:
                return Card.from_dict(yaml.safe_load(f))
    raise FileNotFoundError(card_id)


def _write_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            yaml.dump(data, f, Dumper=yaml.SafeDumper, sort_keys=False, allow_unicode=True)
        os.replace(tmp_name, path)  # atomic on POSIX
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def mtime(card_id: str, root: Path = DATA_DIR) -> float:
    return (root / CARDS / f"{card_id}.yaml").stat().st_mtime


def save(card: Card, expected_mtime: float | None, root: Path = DATA_DIR) -> float:
    """Write a card to cards/. Raises ConflictError if it changed on disk since load."""
    path = root / CARDS / f"{card.id}.yaml"
    if path.exists():
        actual_mtime = path.stat().st_mtime
        if expected_mtime is None or actual_mtime != expected_mtime:
            raise ConflictError(f"{card.id} changed on disk since it was loaded")
    _write_atomic(path, card.to_dict())
    return path.stat().st_mtime


def review(
    card_id: str,
    interested: bool,
    note: str = "",
    root: Path = DATA_DIR,
    today: date | None = None,
) -> Card:
    """The seam: inbox/ -> cards/. Seeds history. Never touches an existing cards/ file."""
    inbox_path = root / INBOX / f"{card_id}.yaml"
    with inbox_path.open() as f:
        card = Card.from_dict(yaml.safe_load(f))

    if interested:
        move(card, "shortlist", note=note, occurred=today)
    else:
        move(card, "archived", reason="passed", note=note, occurred=today)

    _write_atomic(root / CARDS / f"{card.id}.yaml", card.to_dict())
    inbox_path.unlink()
    return card
