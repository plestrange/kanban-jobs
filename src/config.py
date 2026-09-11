from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"

CRITERIA_VERSION = "v1"


def load_criteria(root: Path = DATA_DIR) -> dict:
    path = root / "criteria.yaml"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — run `make init` to create it from config/criteria.example.yaml"
        )
    with path.open() as f:
        data = yaml.safe_load(f)

    version = data.get("version")
    if version != CRITERIA_VERSION:
        raise ValueError(
            f"{path} is at version {version!r}, tool expects {CRITERIA_VERSION!r} — "
            "update the file to the current schema before continuing"
        )
    return data
