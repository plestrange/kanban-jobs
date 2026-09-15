---
name: find-jobs
description: Run a job-search discovery sweep for this repo — finds and screens new listings against data/criteria.yaml and data/profile.md, and writes survivors to data/inbox/ for review in the Discovery tab. Use when the user asks to run a sweep, find new roles, or check for new listings.
---

Follow the procedure in `docs/FIND-JOBS.md` in full, starting with "The one
rule." Do not summarize or skip steps.

Read `data/criteria.yaml` and `data/profile.md` before searching. Read
`data/inbox/*.yaml` and `data/cards/*.yaml` before writing anything, to avoid
re-surfacing candidates already seen or decided.

Never write to `data/cards/`. New candidates go to `data/inbox/` only.
