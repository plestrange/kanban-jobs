# Contributing

Thanks for looking at this. It's a small, deliberately minimal tool — read
`docs/design/ARCHITECTURE.md` before proposing anything structural. Most design
questions ("why isn't there a CLI", "why flat files instead of SQLite", "why
no staleness flags") are already answered there, with the reasoning.

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/) — uv will fetch a
matching interpreter itself if you don't already have one.

```
git clone <your fork>
cd kanban-jobs
make venv   # uv sync — creates .venv from the pinned versions in uv.lock
source .venv/bin/activate
make init   # sets up data/ and installs the pre-commit hook
```

`uv.lock` pins exact versions of every dependency, direct and transitive —
that's what CI installs from too, so what passes locally is what runs there.
Changed a dependency in `pyproject.toml`? Run `uv lock` and commit the
updated `uv.lock` alongside it.

The pre-commit hook's first and most important job is stopping `data/`
(personal search data) from ever being committed — see `docs/design/ARCHITECTURE.md`
§9. It also runs `lint`, `typecheck`, and `test`, in that order, so a commit
that fails any of them is refused up front rather than caught later in CI.
Keep it installed even though you're working on the tool, not the data.

Expect commits to take a few seconds longer because of this — that's the
tradeoff for not finding out about a broken test only when CI runs.

## Before opening a PR

```
make lint        # ruff
make typecheck    # mypy
make test         # pytest + the data/ tracking check
make docs         # confirm the Sphinx build isn't broken
```

The pre-commit hook already runs the first three on every commit; `make docs`
is the one check it doesn't cover, so run it yourself before opening a PR.
All four run in CI on every PR (`.github/workflows/ci.yml`), against Python
3.11 and 3.12. A PR that doesn't pass them won't merge.

## Scope

- Keep changes small and single-purpose. This isn't a CRM and isn't trying to
  become one — see `docs/design/ARCHITECTURE.md` §1 for the stated non-goals before
  adding a field, a flag, or a view.
- New behavior needs a test. `tests/fixtures/` has invented listings at
  fictional companies for exactly this — never add a real listing there.
- If a change touches the data model, the stage machine, or the two-writer
  rule between Job Listings and the Interview Board, update
  `docs/design/ARCHITECTURE.md` alongside the code. That document is the
  design record, not just a description of what happened to get built.
- User-visible changes get a line in `CHANGELOG.md` under `Unreleased`.

## Commit messages

Explain *why*, not just what — see the existing log for the style this repo
uses. No fixed format is enforced, but a message that only restates the diff
isn't pulling its weight.
