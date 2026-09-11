# Job Pipeline

A tool for running a job search: a Claude-driven discovery procedure that
screens listings against your criteria, and a browser board for tracking what
you're doing about them. See `docs/ARCHITECTURE.md` for the full design and
`docs/DISCOVERY.md` for the discovery procedure itself.

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
- `make lint` — ruff
- `make typecheck` — mypy
- `make docs` — build the Sphinx docs into `docs/_build/html`
- `make docs-serve` — serve the docs at http://127.0.0.1:8000, rebuilding on save

## Status

M1–M5 are in place: the core library, the Discovery review queue, the
drag-and-drop board with mtime conflict handling, and card detail (notes,
contacts, referral, an editable history timeline). Per `docs/ARCHITECTURE.md`
§11, M5 is the last milestone — the tool is finished, not paused.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). CI runs lint, typecheck, tests, and
the docs build on every PR.

## License

MIT — see [LICENSE](LICENSE). Changes are tracked in
[CHANGELOG.md](CHANGELOG.md).
