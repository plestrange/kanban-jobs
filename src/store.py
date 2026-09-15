from __future__ import annotations

import os
import tempfile
from datetime import date
from pathlib import Path

import yaml

from .config import DATA_DIR
from .models import Listing
from .pipeline import move

LISTINGS = "listings"
INTERVIEW_BOARD = "interview-board"


class ConflictError(Exception):
    """Raised when a save's expected_mtime no longer matches the file on disk."""


def _str_presenter(dumper: yaml.SafeDumper, data: str):
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


yaml.add_representer(str, _str_presenter, Dumper=yaml.SafeDumper)


def _load_dir(dir_path: Path) -> list[Listing]:
    if not dir_path.exists():
        return []
    listings = []
    for path in sorted(dir_path.glob("*.yaml")):
        with path.open() as f:
            data = yaml.safe_load(f)
        listings.append(Listing.from_dict(data))
    return listings


def load_listings(root: Path = DATA_DIR) -> list[Listing]:
    return _load_dir(root / LISTINGS)


def load_interview_board(root: Path = DATA_DIR) -> list[Listing]:
    return _load_dir(root / INTERVIEW_BOARD)


def load(listing_id: str, root: Path = DATA_DIR) -> Listing:
    for sub in (INTERVIEW_BOARD, LISTINGS):
        path = root / sub / f"{listing_id}.yaml"
        if path.exists():
            with path.open() as f:
                return Listing.from_dict(yaml.safe_load(f))
    raise FileNotFoundError(listing_id)


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


def mtime(listing_id: str, root: Path = DATA_DIR) -> float:
    return (root / INTERVIEW_BOARD / f"{listing_id}.yaml").stat().st_mtime


def save(listing: Listing, expected_mtime: float | None, root: Path = DATA_DIR) -> float:
    """Write to interview-board/. Raises ConflictError if it changed on disk since load."""
    path = root / INTERVIEW_BOARD / f"{listing.id}.yaml"
    if path.exists():
        actual_mtime = path.stat().st_mtime
        if expected_mtime is None or actual_mtime != expected_mtime:
            raise ConflictError(f"{listing.id} changed on disk since it was loaded")
    _write_atomic(path, listing.to_dict())
    return path.stat().st_mtime


def review(
    listing_id: str,
    interested: bool,
    note: str = "",
    root: Path = DATA_DIR,
    today: date | None = None,
) -> Listing:
    """The seam: listings/ -> interview-board/. Seeds history. Never touches an existing
    interview-board/ file."""
    listing_path = root / LISTINGS / f"{listing_id}.yaml"
    with listing_path.open() as f:
        listing = Listing.from_dict(yaml.safe_load(f))

    if interested:
        move(listing, "shortlist", note=note, occurred=today)
    else:
        move(listing, "archived", reason="passed", note=note, occurred=today)

    _write_atomic(root / INTERVIEW_BOARD / f"{listing.id}.yaml", listing.to_dict())
    listing_path.unlink()
    return listing
