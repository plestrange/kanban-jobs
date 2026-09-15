# Concepts

This tool has 2 separate views for different stages of looking for a new job:
1. Searching through job listings and findings which ones to apply to
2. Keeping track of the application and interview process for each job

## The 2 views

Job Listings and the Interview Board are two separate programs that happen to share a
directory:

| | Job Listings | Interview Board |
|---|---|---|
| Runs | A Claude session, by hand, monthly-ish | The Flask app, whenever you open it |
| Writes | `data/listings/` | `data/interview-board/` |
| Cadence | Episodic, batch | Continuous, one card at a time |

**Job Listings** is the review queue: one row per candidate the last sweep
found, with the fit assessment (tier, comp, why/gap) it wrote against your
profile, and two actions — **Interested** or **Pass**.

```{image} _static/screenshots/listings.jpg
:alt: The Job Listings queue, showing one candidate's tier, comp, and fit assessment with Interested/Pass actions
:width: 700px
```

**The Interview Board** is the kanban — listings you've already decided to pursue,
grouped into columns by stage, showing how long each has sat where it is.

```{image} _static/screenshots/interview-board.jpg
:alt: The Interview Board, showing kanban columns per stage with a listing in each
:width: 700px
```

Reviewing a candidate in the Job Listings queue moves it into the board either into
one of the columns or into the Archive for future reference.

See [Running a job search sweep](guide.md#running-a-job-search-sweep) and
[The Job Listings queue](guide.md#the-job-listings-queue).

## The tool, and your data

This repo is a tool: a listing schema, a stage machine, a job search
procedure, and the two views above. It's generic and versioned, and nothing
about it changes between one job search and the next.

Your data — criteria, candidates, notes, comp conversations — is yours
alone. It lives in `data/`, a gitignored directory at the repo root, and
never enters git history. Fork the tool; your data stays local to your
checkout.

```
data/
  criteria.yaml            # your rubric, exclusions, thresholds
  profile.md               # your background, for assessing fit
  listings/<id>.yaml        # search output, awaiting review
  interview-board/<id>.yaml # everything you've decided about
```

`config/criteria.example.yaml` and `config/profile.example.md` are the
templates `make init` copies into `data/` — the schema, with no personal
content.

## The listing lifecycle

Every job posting is one YAML file, for its whole life:

1. A job search sweep writes `listings/<id>.yaml` with everything it found and
   assessed — company, title, comp, location, and a `why`/`gap` fit
   assessment written against your `profile.md`.
2. You review it in the Job Listings tab and mark it **Interested** or
   **Pass**. Either action moves the file to `interview-board/<id>.yaml` —
   Interested at stage `shortlist`, Pass at stage `archived`.
3. From there it's yours. The Interview Board reads and writes
   `interview-board/`; a sweep never looks at it again except to avoid
   re-surfacing it.

A listing's discovery data — the fields from step 1 — freezes at the moment
it's promoted. The Interview Board only ever adds to the pipeline half of the
file: `stage`, `history`, `contacts`, `referral`, `notes`.

Doing nothing is a valid choice: a listing you neither mark Interested nor
Pass just stays in `listings/`, unreviewed, until you decide.

## Stages and archiving

```
shortlist → applied → informational → technical → take-home → panel → offer
```

plus one `archived` lane, for anything you're no longer pursuing regardless
of why. `reason` (`passed`, `rejected`, `withdrew`, `expired`, `other`)
records which, alongside the stage.

A listing can move to any stage from any other — there's no workflow to
satisfy, so moving straight from `applied` to `offer`, or backing a listing
up a column because you misfiled it, both just work.

Archiving is permanent as far as job search sweeps are concerned: a sweep
never re-surfaces a listing once it's archived, whatever the reason. Nothing
is ever deleted — `interview-board/archived` is the full record of
everything you've decided about, not a trash can.

## Time is shown, not judged

Every listing shows `days_in_stage` — how long it's sat where it is, computed
from when it last moved. That's the entire signal the Interview Board gives
you about time. There's no due-date field, no staleness flag, no "needs
attention" sort. Whether a long `days_in_stage` means *follow up* or
*they're just slow* is a judgment about that company and that recruiter, and
it's yours to make — the tool only has the number, not the context behind it.

Stage moves take an optional date, defaulting to today, so you can backdate
a move you're logging late without lying about how long the listing's
actually been there.
