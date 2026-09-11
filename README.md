# Job Pipeline

A tool for running a job search: a Claude-driven discovery procedure that
screens listings against your criteria, and a browser board for tracking what
you're doing about them. See `ARCHITECTURE.md` for the full design and
`DISCOVERY.md` for the discovery procedure itself.

The tool lives here, in git. Your data — criteria, candidates, notes — lives
in a gitignored `data/` directory and never gets committed.

## Setup

```
make init   # creates data/, copies config/criteria.example.yaml, installs the pre-commit hook
```

Then edit `data/criteria.yaml` and write `data/profile.md` before running a
discovery sweep.

## Commands

- `make dev` — run the app
- `make test` — run the test suite and check no data/ paths are tracked
- `make check-clean` — just the data/ tracking check

## Status

M1–M3 are in place: the core library (`core/config.py`, `models.py`,
`store.py`, `pipeline.py`, `views.py`), the Discovery review queue, and a
read-only, server-rendered board. M4 (drag-and-drop) is next — see
`ARCHITECTURE.md` §11 for the build order.
