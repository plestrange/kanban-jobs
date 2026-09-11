# Discovery Procedure

Instructions for a Claude session running a discovery sweep. Read this in full
before starting.

Discovery finds candidate listings, screens them against the user's criteria, and
writes them to `data/inbox/` for the user to review in the Discovery
tab. It is a judgment task, not a scraper — the value is in the screening, not
the volume.

This is the only thing discovery does. It is a Claude session, started by hand,
monthly-ish. Nothing here runs on a schedule and nothing re-checks cards already
in play.

---

## The one rule

**Never write to `data/cards/`.**

`cards/` holds listings the user has already reviewed and is actively working. A
discovery pass writes **only** `inbox/`. It reads `cards/` — that's how it avoids
re-surfacing things the user already decided about — and it never writes there.

If a pass learns that a card in play has changed — posting closed, comp range
moved, duplicate found under a new req — it **says so in the closing summary** and
stops. There is no file it writes and no badge it raises. The user decides what to
do with it, in the app, by hand.

Rewriting a card mid-interview-loop is the one failure this whole design exists
to prevent.

---

## Inputs

| File | What it gives you |
|---|---|
| `data/criteria.yaml` | Titles, level, location rules, exclusions, watchlist, fit rubric |
| `data/profile.md` | The user's background — what the fit assessment is written *against* |
| `data/inbox/*.yaml` | Already-surfaced candidates awaiting review |
| `data/cards/*.yaml` | Already-decided listings — including passed ones |

All paths are relative to the repo root. There is no environment variable to
resolve and no configured location — see ARCHITECTURE.md §2.

Read all four before searching. Skipping the last two is how a run hands the user
twenty roles they already rejected.

---

## Phase 1 — Frame

1. Read `criteria.yaml` and `profile.md`.
2. Build the **seen set**: every `req_id`, and every `(company, normalized title,
   location)` triple, across `inbox/` and `cards/`.
3. Build query templates from the criteria — the cross product of
   `titles + title_aliases` against `location.accept`. The search terms are
   rarely the posted titles: a role advertised as "ML Platform Engineer" or
   "Senior Software Engineer, ML Systems" is often the same job as "MLOps
   Engineer". `title_aliases` exists for this; use it.

---

## Phase 2 — Sweep

Breadth first. Collect candidates with whatever metadata each source gives,
without deep-fetching individual postings yet.

### ATS APIs — start here

Most applicant tracking systems publish a per-company job board as public JSON.
No authentication, no scraping, structured fields, and far more reliable than
parsing a board's HTML. Greenhouse, Lever and Ashby all expose one.

Use these for the **watchlist** in `criteria.yaml` — companies the user wants
monitored regardless of whether a board surfaces them. Polling a dozen target
companies directly is higher-yield than any keyword search.

This also solves Ashby: their postings are JavaScript-rendered and unreadable
through a normal fetch, but their posting API returns the same content as JSON.

*Verify the exact endpoint shape on first use and record it in the repo — these
URLs change occasionally and are easier to confirm than to remember.*

### Aggregator boards — for breadth

Where you find companies not on the watchlist. Most surface posted salary ranges,
which is the single most useful screening field.

- **Built In** (`builtin.com`, city sites like `builtinseattle.com`) — best
  coverage of mid-to-large companies, reliably shows comp and work arrangement.
- **RemoteRocketship** — strongest for remote roles; lists state restrictions
  up front, which is a hard filter you can apply without fetching anything.
- **hiddenjobs.dev** — smaller companies that don't reach the big boards.
- **startup.jobs** — startup-weighted, thinner metadata.
- **fastaijobs.com** — ML/AI-specific, but heavily padded with adjacent network
  and datacenter roles that aren't ML at all. Screen hard.
- **Hacker News "Who is hiring?"** (`hnhiring.com`) — monthly thread, good for
  companies invisible to every board above. Low signal-to-noise; one pass, not
  more.

### Sources that don't work

- **LinkedIn, Indeed, Glassdoor, ZipRecruiter** — login-walled or bot-blocked.
  They surface in search results and rarely fetch.

**Do not ask the user for credentials to these sites, and do not accept them if
offered.** Automated access to a logged-in LinkedIn session violates their terms
and risks the account — which is the user's actual professional network. If they
want LinkedIn coverage, the route is Claude in Chrome on their own machine,
driving their own authenticated browser with them present. Note it and move on.

---

## Phase 3 — Identity and dedupe

**Two openings at one company can share a title.** Two Expedia "Machine Learning
Engineer III" postings on different teams are different candidates, not
duplicates. Meanwhile the *same* role routinely appears on three boards under
three URLs. Dedupe has to separate these cases.

**`req_id` is the identity.** Every ATS puts a stable requisition id in the URL:

| ATS | Example URL fragment | `req_id` |
|---|---|---|
| Greenhouse | `/jobs/6097372004` | `6097372004` |
| Workday | `..._jr2023055` | `jr2023055` |
| Lever | `/jobs.lever.co/co/<uuid>` | the uuid |
| Rippling | `/jobs/<uuid>` | the uuid |

**Rules, in order:**

1. **Resolve to the ATS URL before deduping.** An aggregator listing usually
   links through to one. This is worth doing early — it gives you identity, a
   more durable URL, and the authoritative posting text in one step.
2. **Same `req_id` → same role.** Collapse, keep the ATS URL.
3. **No `req_id` available** (aggregator-only listing) → fall back to
   `(company, normalized title, location)`. Normalize by lowercasing, stripping
   seniority prefixes and location suffixes, collapsing whitespace.
4. **Same company and title, different `req_id` → two candidates.** Record the
   `team` for each so the user can tell them apart, and give each a distinct
   filename (see below).

A candidate already in `cards/` at stage `archived` is one the user is not
continuing with — passed on, rejected, withdrawn from, or expired. Do not
re-surface it, whatever the `reason` says. That is the entire reason archived
cards are kept rather than deleted.

### Filenames

`<company-slug>-<role-slug>.yaml`, e.g. `mercury-sr-mlops.yaml`. On collision,
append a short discriminator — the team slug where it's meaningful, otherwise the
last five characters of `req_id`:

```
expedia-mle-iii-layla.yaml
expedia-mle-iii-lodging.yaml
```

The `id` field inside the file always matches the filename stem.

---

## Phase 4 — Screen on cheap signals

Apply hard filters **before** deep-fetching. Fetching is the expensive step; most
candidates die here on metadata you already have.

In order:

1. **Employer exclusions** from `criteria.yaml`.
2. **Sector exclusions** — judge by what the company does, not what the posting
   says.
3. **Location eligibility.** State-restricted remote ("CA and MA only"), timezone
   requirements ("East Coast hours"), onsite-only, and relocation all fail. A
   Seattle-based user cannot take a role restricted to California residents, no
   matter how good the fit — record it with `eligible: false` and `tier: out`
   rather than discarding it, so the next sweep doesn't rediscover it.
4. **Level.** Below the criteria's `level.min` fails.
5. **Reach content.** Per the rubric's `drop` rule, roles whose core technical
   content is a genuine stretch get dropped, not ranked. Be honest; a generous
   tier is worse than no entry.

---

## Phase 5 — Verify and assess

For each survivor, fetch the ATS posting. Set `url_kind` to record whether the
stored URL is `ats` or `aggregator` — aggregator links rot far faster.

Confirm and extract:

- **Still open.** A closed or 404 posting is not a candidate.
- **`req_id` and `team`.** Both come from the posting or its URL.
- **Comp range as posted.** Never estimate into the `comp` block; `source: none`
  is honest and an invented range is not.
- **Location and remote policy as the employer states it.** Aggregators get this
  wrong often — "in-office" on a board frequently means hybrid in the posting.
  Where they disagree, trust the ATS and note the discrepancy.
- **Required experience and named stack.**

Then write the assessment against `profile.md`:

- **`tier`** — per the rubric.
- **`why`** — what in this posting describes work the user has already shipped.
  Specific. "Real-time inference service, model registry, staged rollouts, drift
  detection" beats "good MLOps fit".
- **`gap`** — the specific requirement they don't have. Per `criteria.yaml`'s
  `candor` setting, name it plainly. A gap the user discovers in a recruiter
  screen is a gap this file failed to name.

---

## Phase 6 — Write

**New candidates** → one `inbox/<id>.yaml` per survivor, schema per
ARCHITECTURE.md §5.2. Fill the discovery zone completely; leave the pipeline zone
out entirely — the app writes it at review.

Always set `discovered.via` to the source that surfaced it. After a few sweeps
this tells you which sources produce candidates that get shortlisted and which to
stop querying.

**Existing cards** → nothing is written, ever. If the sweep noticed something
about a card in play, it goes in the closing summary as a sentence:

> Anthropic ML Platform (card at stage `technical`): the original Greenhouse
> posting 404s, but the same role is live at req 6141572004 with the range raised
> to $180k–$225k.

Short and factual, in conversation. Do not write a file and do not edit the card.

---

## Volume

Cap a sweep at roughly **25 new candidates**, prioritized by tier. If the sweep
found more, keep the strongest and say so in your summary.

Not a technical limit. Twenty cards is a review session the user will sit down
and clear; two hundred is a chore they'll skip, and a skipped queue means a stale
board. Small and frequent beats large and rare.

---

## Referral lookup — optional, and not part of a sweep

Whether the user knows anyone at a company changes the odds more than almost
anything else on the card. It is worth capturing, and it does **not** belong in
the sweep.

**Why it's separate.** Two reasons, and the second is non-negotiable:

1. **Wrong volume.** A sweep screens dozens of candidates, most of which get
   passed on. Checking connections at all of them is wasted effort. The question
   is only worth asking about the handful the user has already shortlisted.
2. **It writes to a card.** `referral` lives in the pipeline zone of a card in
   `cards/`, and a discovery session may never write there. See "The one rule".

**So a session never records a referral.** It can *find* the information and
report it in conversation; the user records it in the app's card detail view.
That division is the whole point — if a session finds itself about to edit a
card, it has taken a wrong turn.

**When to do it.** After shortlisting, on the cards the user is actually going to
apply to. A handful at a time.

**How, optionally.** If the user has [Claude in
Chrome](https://support.claude.com/en/articles/12012173-get-started-with-claude-in-chrome)
installed, a session running on their own machine can drive their already
logged-in browser to check connections at a named company. No credentials change
hands; it's their browser and their session, with them present. Use "manually
approve" mode on sites where the account matters.

This is entirely optional. The lookup works just as well done by hand — the
`referral` field doesn't care how it got filled in. And it is a *targeted*
lookup on a named company, not a way to page through job search results in bulk;
that would be the automated access these sites' terms prohibit, arrived at
sideways.

**What gets recorded**, in the card's pipeline zone:

```yaml
referral:
  status: possible          # none | possible | requested | submitted
  via: "Dana Okafor — former Convoy colleague, now on the platform team"
  checked: 2026-09-10
```

Keep it to those three fields. Tracking who introduced whom, when, and what came
of it is the CRM this project is explicitly not building.

---

## What this procedure cannot do

State these plainly rather than working around them:

- Cannot apply to anything.
- Cannot see roles behind logins — LinkedIn, most company talent networks. The
  Chrome route above is a targeted exception for referral lookups, not a way
  around this for bulk discovery.
- Cannot confirm a posting is genuinely open. A live URL means the page exists,
  not that the req is unfilled.
- Cannot judge team quality, manager, or how real a stated remote policy is.
  Those are recruiter-screen questions, and `gap` should say so when it matters.

---

## Finishing

Report to the user:

- How many candidates were surfaced, screened out, and written.
- The tier distribution of what was written.
- Anything notable — a strong-fit role that fails a location filter is worth
  naming, since it may be worth one email asking whether the restriction is
  negotiable.
- Anything noticed about a card already in `cards/` — see Phase 6. Lead with
  these if a card in an active stage is involved.
