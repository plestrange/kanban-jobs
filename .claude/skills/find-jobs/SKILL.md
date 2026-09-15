---
name: find-jobs
description: Run a job search sweep for this repo — finds and screens new listings against data/criteria.yaml and data/profile.md, and writes survivors to data/listings/ for review in the Job Listings tab. Use when the user asks to run a sweep, find new roles, or check for new listings.
---

Follow the procedure in `docs/FIND-JOBS.md` in full, starting with "The one
rule." Do not summarize or skip steps.

Read `data/criteria.yaml` and `data/profile.md` before searching. Read
`data/listings/*.yaml` and `data/interview-board/*.yaml` before writing
anything, to avoid re-surfacing candidates already seen or decided.

Never write to `data/interview-board/`. New candidates go to `data/listings/`
only.
