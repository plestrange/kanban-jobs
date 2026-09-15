# Kanban Jobs

A tool for running a job search: a Claude-driven job search procedure that
screens listings against your criteria, and a browser board for tracking what
you're doing about them. See `docs/design/ARCHITECTURE.md` for the full design and
`docs/FIND-JOBS.md` for the search procedure itself.

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

`make init` copies two templates from the tracked `config/` directory into
the gitignored `data/` directory — fill both in before your first sweep:

- **`data/criteria.yaml`** — titles, level, location rules, exclusions, the
  companies you want watched directly. Comments in the file explain each
  field; see `docs/design/ARCHITECTURE.md` §5.4 for the full reasoning.
- **`data/profile.md`** — your background, written for a job search sweep
  to assess listings against. Section headers guide you through what to
  include; the more specific, the sharper the `why`/`gap` lines on every
  listing.

Then:

```
make dev            # starts the app at http://127.0.0.1:5050
```

The Interview Board is empty until you run a search sweep (below) and review
what it finds in the Job Listings tab.

### Running a job search sweep

Searching isn't a script — it's a Claude session working through
`docs/FIND-JOBS.md`, using `data/criteria.yaml` and `data/profile.md` as
inputs. Open a Claude Code session with this repo as the working directory
and run:

```
/find-jobs
```

(a project skill at `.claude/skills/find-jobs/`, which just points at
`docs/FIND-JOBS.md`) — or ask in plain language, e.g. "run a job search sweep
per docs/FIND-JOBS.md."

It reads your criteria and profile, searches, screens, and writes results to
`data/listings/`. Nothing is added to `data/interview-board/` — reviewing what
landed in the Job Listings tab (mark each **Interested** or **Pass**) is what
moves a candidate onto the Interview Board. Run a sweep by hand, monthly-ish;
nothing here is scheduled or automatic (see `docs/FIND-JOBS.md` for why).

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
  tuning what a sweep finds and how it's assessed.
- **Interview Board columns** — the stage list lives in `STAGES` in
  `src/models.py`, and each column renders in that order in
  `app/templates/interview-board.html`. Add, remove, or reorder stages there
  if your process doesn't match the default shortlist → … → offer pipeline.
  Existing listings with a stage you removed will fail validation, so update
  any listings in `data/interview-board/` to match.
- **Archive reasons** — `ARCHIVE_REASONS` in `src/models.py`, same idea.

What's load-bearing and worth reading `docs/design/ARCHITECTURE.md` before
touching: the two-writer rule between Job Listings and the Interview Board
(§4), the listing schema (§5.2), and the stated non-goals (§1) — most
requests to add a field or a flag are answered there already.

## Status

M1–M5 are in place: the core library, the Job Listings review queue, the
drag-and-drop Interview Board with mtime conflict handling, and listing
detail (notes, contacts, referral, an editable history timeline). Per
`docs/design/ARCHITECTURE.md` §11, M5 is the last milestone — the tool is
finished, not paused.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). CI runs lint, typecheck, tests, and
the docs build on every PR.

## License

MIT — see [LICENSE](LICENSE). Changes are tracked in
[CHANGELOG.md](CHANGELOG.md).
