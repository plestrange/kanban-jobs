# Kanban Jobs

A tool for running a job search: a Claude-driven discovery procedure that
screens listings against your criteria, and a browser board for tracking what
you're doing about them. See `docs/ARCHITECTURE.md` for the full design and
`docs/FIND-JOBS.md` for the discovery procedure itself.

The tool lives here, in git. Your data — criteria, candidates, notes — lives
in a gitignored `data/` directory and never gets committed. Fork this repo
for your own search; nothing personal ships in it.

## Quickstart

```
git clone <your fork>
cd kanban-jobs
make venv          # uv sync — creates .venv from uv.lock
source .venv/bin/activate
make init           # creates data/, copies the two templates below, installs the pre-commit hook
```

`make init` copies two templates into the gitignored `data/` directory —
fill both in before your first sweep:

- **`data/criteria.yaml`** — titles, level, location rules, exclusions, the
  companies you want watched directly. Comments in the file explain each
  field; see `docs/ARCHITECTURE.md` §5.4 for the full reasoning.
- **`data/profile.md`** — your background, written for a discovery session
  to assess listings against. Section headers guide you through what to
  include; the more specific, the sharper the `why`/`gap` lines on every
  card.

Then:

```
make dev            # starts the app at http://127.0.0.1:5050
```

The board is empty until you run a discovery sweep (below) and review what
it finds in the Discovery tab.

### Running a discovery sweep

Discovery isn't a script — it's a Claude session working through
`docs/FIND-JOBS.md`, using `data/criteria.yaml` and `data/profile.md` as
inputs. Open a Claude Code session with this repo as the working directory
and ask it to run one, e.g.:

> Run a discovery sweep per docs/FIND-JOBS.md.

It reads your criteria and profile, searches, screens, and writes results to
`data/inbox/`. Nothing is added to `data/cards/` — reviewing what landed in
the Discovery tab (mark each **Interested** or **Pass**) is what moves a
candidate onto the board. Run a sweep by hand, monthly-ish; nothing here is
scheduled or automatic (see `docs/FIND-JOBS.md` for why).

## Commands

- `make venv` — (re)create `.venv` via `uv sync`, from the pinned versions
  in `uv.lock`
- `make init` — create `data/`, seed it from the `config/` templates, install
  the pre-commit hook
- `make dev` — run the app at http://127.0.0.1:5050
- `make test` — run the test suite and check no data/ paths are tracked
- `make check-clean` — just the data/ tracking check
- `make lint` — ruff
- `make typecheck` — mypy
- `make docs` — build the Sphinx docs into `docs/_build/html`
- `make docs-serve` — serve the docs at http://127.0.0.1:8000, rebuilding on save

## Making it yours

This is meant to be forked and adjusted, not just run as-is. What's safe to
change without fighting the design:

- **Criteria and profile** — `data/criteria.yaml` and `data/profile.md` are
  entirely yours; edit them freely, any time. They're the intended lever for
  tuning what discovery finds and how it's assessed.
- **Board columns** — the stage list lives in `STAGES` in `src/models.py`,
  and each column renders in that order in `app/templates/board.html`. Add,
  remove, or reorder stages there if your process doesn't match the default
  shortlist → … → offer pipeline. Existing cards with a stage you removed
  will fail validation, so update any cards in `data/cards/` to match.
- **Archive reasons** — `ARCHIVE_REASONS` in `src/models.py`, same idea.

What's load-bearing and worth reading `docs/ARCHITECTURE.md` before touching:
the two-writer rule between Discovery and the board (§4), the card schema
(§5.2), and the stated non-goals (§1) — most requests to add a field or a
flag are answered there already.

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
