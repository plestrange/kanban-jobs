# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Unreleased

### Added

- `.claude/skills/find-jobs/` — a project skill so a discovery sweep can be
  run with `/find-jobs` instead of typing out the full prompt. It's a thin
  pointer at `docs/FIND-JOBS.md`, which stays the single source of truth for
  the procedure.
- `config/profile.example.md` — a template for `data/profile.md`, copied by
  `make init` the same way `criteria.example.yaml` already was. Closes the
  gap where a new user had to dig through `ARCHITECTURE.md` to learn what
  the file should contain.
- README: a real Quickstart walkthrough, an explanation of how a discovery
  sweep actually gets run (it's a Claude session, not a script), and a
  "Making it yours" section pointing at what's safe to customize (criteria,
  profile, board stages, archive reasons) versus what's load-bearing.
- `CONTRIBUTING.md` and this changelog.
- CI (GitHub Actions): lint, typecheck, test, and docs build on every PR,
  against Python 3.11 and 3.12.
- `LICENSE` (MIT).
- Sphinx documentation (`make docs`, `make docs-serve`), with `myst-parser`
  rendering `docs/ARCHITECTURE.md` and `docs/FIND-JOBS.md` directly.
- `make lint` (ruff) and `make typecheck` (mypy).
- `make venv`, backed by `uv` and `uv.lock` — exact, reproducible dependency
  versions instead of `>=` floors, used identically by local dev and CI.

### Changed

- `hooks/pre-commit` now runs `make lint`, `make typecheck`, and `make test`
  after the existing `data/` guard, so a broken commit is caught locally
  instead of only in CI. `make init` re-installs the hook, so existing
  checkouts pick this up the next time they run it.
- `DISCOVERY.md` renamed to `FIND-JOBS.md` — a more descriptive name for
  the procedure it documents.
- Project renamed from Job Pipeline to Kanban Jobs, ahead of publishing.
- Machine-wide Python management moved to pyenv (global default 3.12.14);
  the interpreter version for this project itself is governed by
  `pyproject.toml`'s `requires-python` and resolved by `uv`, not a tracked
  `.python-version` file.
- `core/` renamed to `src/`.
- `ARCHITECTURE.md` and `DISCOVERY.md` moved into `docs/`.
- `hooks/pre-commit` and `scripts/check-clean.sh` folded into Makefile
  targets (`check-clean`, `check-staged`) sharing one pattern, instead of
  two scripts that could drift apart.
- `ARCHITECTURE.md` moved to `docs/design/`, separating the design record
  (decisions, rejected alternatives, reasoning) from user-facing docs, which
  are being rewritten as a streamlined guide.
- Renamed the two views and their data folders for clarity: Discovery is now
  **Job Listings** (`data/listings/`, was `data/inbox/`) and Board is now
  the **Interview Board** (`data/interview-board/`, was `data/cards/`). The
  `Card` model, routes, templates, and static assets were renamed to match
  (`Card` → `Listing`, `/board` → `/interview-board`, `/discovery` →
  `/listings`, etc). The `/find-jobs` skill and procedure name are unchanged;
  the search process itself is now called a "job search sweep" rather than
  "discovery" throughout the docs.

## 0.1.0

The tool as built through milestones M1–M5 (see `docs/design/ARCHITECTURE.md` §11):

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
