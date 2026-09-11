# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Unreleased

### Added

- `CONTRIBUTING.md` and this changelog.
- CI (GitHub Actions): lint, typecheck, test, and docs build on every PR,
  against Python 3.11 and 3.12.
- `LICENSE` (MIT).
- Sphinx documentation (`make docs`, `make docs-serve`), with `myst-parser`
  rendering `docs/ARCHITECTURE.md` and `docs/DISCOVERY.md` directly.
- `make lint` (ruff) and `make typecheck` (mypy).
- `make venv`, backed by `uv` and `uv.lock` — exact, reproducible dependency
  versions instead of `>=` floors, used identically by local dev and CI.

### Changed

- Machine-wide Python management moved to pyenv (global default 3.12.14);
  the interpreter version for this project itself is governed by
  `pyproject.toml`'s `requires-python` and resolved by `uv`, not a tracked
  `.python-version` file.
- `core/` renamed to `src/`.
- `ARCHITECTURE.md` and `DISCOVERY.md` moved into `docs/`.
- `hooks/pre-commit` and `scripts/check-clean.sh` folded into Makefile
  targets (`check-clean`, `check-staged`) sharing one pattern, instead of
  two scripts that could drift apart.

## 0.1.0

The tool as built through milestones M1–M5 (see `docs/ARCHITECTURE.md` §11):

### Added

- Core library: card schema, YAML store with atomic writes and mtime-based
  conflict detection, the stage-transition pipeline, and derived views.
- Discovery review queue (M2): a keyboard-driven queue for marking inbox
  candidates Interested or Pass.
- Read-only, server-rendered board (M3).
- Drag-and-drop between board columns (M4), with an inline reason/note
  prompt when archiving and a visible snap-back on a write conflict.
- Card detail view (M5): notes, contacts, referral, and an editable history
  timeline (`occurred` date and note per entry; `recorded` stays immutable).
- `DISCOVERY.md`: the procedure a Claude session follows to run a search
  sweep, kept generic against whatever `criteria.yaml` it's pointed at.
