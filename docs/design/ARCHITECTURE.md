# Kanban Jobs — Architecture Plan

**Status:** decided — ready to hand to a desktop session to build
**Date:** 6 September 2026

**Decided:** core library + browser app with **two views** (Discovery, Board);
**flat YAML files**, one per listing; data in a gitignored `data/` inside the
repo, kept out of git by the hook in §9.
Board columns: Shortlist → Applied → Informational → Technical → Take-home →
Panel → Offer, plus one Archived lane. All open items are now decided; §10 keeps
the record.

---

## 1. Intent

Two separable things:

- **A tool** that knows how to search for listings against a rubric and run a
  pipeline board. Generic, versioned, reusable for the next search or by anyone
  else. Lives in git.
- **A dataset** — your criteria, your candidates, your status, your notes. Yours
  alone, never committed.

**Success looks like:** the board shows the true state of every application at a
glance; re-running the search applies the same rubric rather than re-deriving it;
the repo could be made public tomorrow without redacting anything.

**Non-goals**, each of which would double the build:

- **Not an advisor.** This is a filing cabinet, not a system that tells you what
  to do. It shows you what you have and what state it's in, accurately and
  legibly; deciding what deserves attention today is yours. Anything that ranks,
  flags, nags or prioritises has to justify itself against that, and most of it
  can't — see §5.5.
- Not a CRM. No email integration, no calendar sync, no automated follow-ups.
- No auto-apply, no resume tailoring.
- No scraping. Discovery stays a judgment task run in a Claude session; the repo
  holds the *procedure*, your config holds the *criteria*.
- Single user. No auth, no accounts, no sharing.

**The honest case for the repo.** Not the twenty listings — those are a snapshot
with a short shelf life. What's worth versioning is the machinery: the card
schema, the stage machine, the two views, and the written discovery procedure.
That's a thing you can point at a new search in a year, and it stays useful after
this search closes.

---

## 2. The tool/data boundary

**Nothing personal enters the repo.** Not the listings, not the statuses, not the
notes, and not the criteria — an exclusion list naming employers is an opinion
about the industry you work in, and it belongs with your data.

### Where the data lives

**`data/`**, at the repo root, gitignored. A fixed path, not a configured one.

```
data/
  criteria.yaml          # your rubric, exclusions, thresholds
  profile.md             # your background — what fit is assessed against
  inbox/<id>.yaml        # discovery output, awaiting review
  cards/<id>.yaml        # everything you've decided about
```

**There is no `$JOBS_DATA_DIR` and no setting for this.** An earlier draft made
the location an environment variable so it could be overridden. Once the data
moved inside the repo (below) that override stopped paying for itself: one
checkout, one search, one machine. Putting the path in `criteria.yaml` instead
doesn't work either — that file *is* `data/criteria.yaml`, so the location would
be configured by a file you can't find until you know the location.

The one real consumer of an override was the test suite, and §6.1 gives it a
better one: `store.py` functions take a `root` argument, defaulting to `data/`.
Tests pass a fixture directory; nothing else ever passes anything. What's gone is
a concept in the docs and a failure mode — set in one shell and not another, or
set wrong and silently reading an empty board.

If you ever want a second search with separate data, copy the repo. With the data
inside it, that's the natural gesture anyway.

`profile.md` is the piece `criteria.yaml` doesn't cover: the rubric says *how* to
judge fit, but the `why` and `gap` lines are written against what you've actually
shipped. Derived from your resume and written for this purpose — current role and
level, stack, domains worked in, what you're optimizing for. A discovery session
that can't read this can apply the filters but can't assess anything.

**Why inside, and what it costs.** One folder holds the tool and the data: one
thing to back up, one thing to copy to another machine, no environment variable
to set or forget, and a relative path a discovery session can write without
resolving anything first. That convenience is real and it's the reason for the
choice.

The cost is that the separation is now enforced by configuration rather than by
geography. Data outside the repo can't be committed by accident because the
mistake isn't available to you; data inside is one `git add -f`, one bad merge or
one careless `.gitignore` edit away — and once recruiter names and comp notes are
in history, they're in history.

**So §9 stops being defense in depth and becomes the mechanism.** The pre-commit
hook is no longer optional belt-and-braces; it is the thing standing between you
and an unrecoverable commit, and `make init` installs it rather than the README
merely describing it. §1's claim that the repo could be made public tomorrow now
rests on that hook having worked every time, not on the data being somewhere the
repo can't see.

### No version control over the data

`data/` is gitignored and stays that way. Recruiter names, comp conversations and
interview notes don't belong in a commit log — not this repo's, and not one of
their own.

What replaces it: each card carries its own `history` array, so stage changes are
recorded in the card itself. For everything else, ordinary file backup is the
safety net — whatever already backs up your home directory covers this. The
tradeoff being accepted: an accidental bad edit to a card is unrecoverable beyond
that backup. At this scale that's the right trade.

### What ships instead

- `config/criteria.example.yaml` — the full schema with placeholder values and
  comments. Copied to `data/criteria.yaml` by `make init`.
- `config/profile.example.md` — a template with section headers and no
  personal content. Copied to `data/profile.md` by `make init`.
- `tests/fixtures/` — **invented** cards at fictional companies. Not scrubbed
  real ones; scrubbing leaks, and `acme-sr-mlops` is clearer anyway.
- `FIND-JOBS.md` — the procedure a Claude session follows, written generically
  against whatever `criteria.yaml` it's pointed at.

---

## 3. Storage: flat files, not SQLite

Decided in favour of YAML files. The reasoning, since it's the kind of decision
that gets revisited:

**Why files win here**

- **Discovery is a Claude session writing files.** With YAML that's plain writes,
  with no dependency on the tool being installed or working. With SQLite the
  session shells out to `sqlite3` with hand-written SQL against a schema it must
  be told about, and a botched INSERT corrupts the store rather than producing a
  malformed file you can open in vim. That couples discovery to the tool's
  runtime — exactly what §4 works to avoid.
- **Hand-editable.** You can fix a card in vim when the app is broken or
  half-built, and jot a note faster than any UI will let you. During M1–M3 this
  is the *only* way to edit anything.
- **Greppable and inspectable.** `grep -l "stage: technical" cards/*.yaml` needs
  no tooling and no schema knowledge. Answering "what's actually in my data
  right now" never requires the app to be running.

Note what is *not* an argument here: the data is not under version control (§2),
so YAML's diffability buys nothing. The case rests on the two points above.

**What SQLite would buy, and why it doesn't apply**

| SQLite advantage | Why it isn't needed here |
|---|---|
| Atomic writes | `os.replace()` on a temp file is atomic on POSIX |
| Concurrency | One user; the mtime check in §6.3 covers the rest |
| Query performance | ~300 small files load in ~50ms; views are list comprehensions |
| Migrations | Adding a YAML key with a default is not a migration |

**What would change the answer:** multi-device concurrent editing, thousands of
records, or transactions spanning multiple cards. None apply.

**The escape hatch, if the board ever gets slow:** build a SQLite *index* derived
from the files, rebuilt on change. Query the index, keep the truth in YAML. Don't
move the truth into the database.

---

## 4. Two systems, one contract

Discovery and tracking are **two programs sharing a directory**, not one app with
two features:

| | Discovery | Board |
|---|---|---|
| Cadence | Episodic — monthly-ish | Continuous — daily |
| Driver | Claude session | You |
| I/O | Network-bound, batch writes | Local, one card at a time |
| Failure mode | Stale or wrong data | Lost state |

### The rule: no file ever has two writers

- **Discovery writes only** `inbox/`.
- **The app writes only** `cards/`.
- Neither ever writes the other's directory. No exceptions, no "just this field".

A card's discovery data **freezes at promotion**, and nothing ever unfreezes it.
If a later sweep learns something about a card in play — posting closed, range
changed, duplicate surfaced — it says so in its summary and stops there. There is
no channel back into a card you're working. You decide what, if anything, to do
with it.

An earlier draft gave discovery a side channel (`alerts/<id>.md`, rendered as a
badge) plus a cron'd health check that re-fetched active cards' URLs. Both were
cut. They existed to answer "has this posting changed?", and answering it changes
nothing: the card already shows how long it has sat where it is, and you follow
up, or don't, on that. A directory, a file format, a parser, a read-state field,
a badge and a sort tier is a lot of machinery to buy a fact you won't act on.

### The seam is the Discovery view's review action

The two systems meet at exactly two places: the card schema, and one gesture —
marking a candidate. Discovery drops cards in `inbox/`; you review them in the
Discovery tab and mark each **Interested** or **Pass**. Either action moves the
file from `inbox/` to `cards/` and it's yours from then on.

Either program can be rewritten without the other noticing.

---

## 5. Data model

### 5.1 One file per listing

`inbox/<id>.yaml` before review, `cards/<id>.yaml` after. One move per card, for
its whole life.

**Stage is a field, not a directory** — a move rewrites one line in place rather
than relocating a file, which keeps every card at a stable path you can open,
link to, or hand-edit regardless of where it sits in the pipeline. **Archived
cards stay in `cards/`**; `archived` is a stage like any other.

**Passing on a candidate writes the card, it doesn't delete it.** `Pass` promotes
to `cards/` with stage `archived`. This is what stops the next discovery run
re-surfacing something you already rejected, and it keeps `cards/` as the single
record of everything you've decided about.

**Doing nothing is deferral.** A card you neither accept nor pass stays in
`inbox/`. No button needed.

**ID scheme:** `<company-slug>-<role-slug>`, e.g. `mercury-sr-mlops`. Company
alone collides the first time somewhere posts two roles you both want.

**Identity is `req_id`, not the filename.** One company routinely posts two
openings with the *same* title on different teams, while the *same* opening
appears on three boards under three URLs. Neither case resolves on company plus
title. Every ATS puts a stable requisition id in the URL — Greenhouse
`/jobs/6097372004`, Workday `_jr2023055`, Lever and Rippling a uuid — and that is
the authoritative identifier. Store it as `req_id`; dedupe on it; fall back to
`(company, normalized title, location)` only for aggregator-only listings that
never resolved to an ATS.

On a filename collision, append the team slug where it's meaningful, otherwise
the last five characters of `req_id`: `expedia-mle-iii-layla`,
`expedia-mle-iii-lodging`.

### 5.2 Card schema

Two zones in one file, separated by an ownership boundary the writer code honors:

```yaml
# ═══ discovery zone — written by search sessions, frozen at promotion ═══
id: mercury-sr-mlops
req_id: "6097372004"              # from the ATS URL — the real identity
company: Mercury
title: Senior Machine Learning Operations Engineer
team: "Risk Platform"             # distinguishes same-title reqs; null if unstated
location:
  mode: remote                    # remote | hybrid | onsite
  scope: "US, Canada"
  eligible: true                  # false when state- or timezone-restricted
comp: {min: 166600, max: 208300, currency: USD, source: posted}
url: https://job-boards.greenhouse.io/mercury/jobs/6097372004
url_kind: ats                     # ats | aggregator — see Risks
discovered: {date: 2026-09-06, via: "greenhouse search", rubric: v1}
assessment:
  tier: strong                    # strong | good | out
  why: >
    Real-time inference service, model registry and staged rollouts, drift
    detection, and owning the handoff from data scientists into production.
  gap: >
    Kafka/Kinesis streaming and Redis/DynamoDB stores are named requirements
    and aren't on the resume.
company_summary: "Fintech banking platform for startups."  # one line, at a glance

# ═══ pipeline zone — written by the app, yours alone ═══
stage: technical                  # stored, not derived — see below
reason: null                      # only when stage is archived; see §5.3
history:                          # occurred = the world; recorded = the board
  - {occurred: 2026-09-08, recorded: 2026-09-08, to: shortlist,     note: ""}
  - {occurred: 2026-09-09, recorded: 2026-09-09, to: applied,       note: "referred by K. Ito"}
  - {occurred: 2026-09-15, recorded: 2026-09-16, to: informational, note: "30min recruiter call"}
  - {occurred: 2026-09-22, recorded: 2026-09-25, to: technical,     note: "systems design, 90min"}
contacts:
  - {name: "Kenji Ito", role: recruiter, note: ""}
referral:
  status: possible                # none | possible | requested | submitted
  via: "Dana Okafor — former Convoy colleague, now on the platform team"
  checked: 2026-09-10
notes: |
  Free text. Interview prep, questions to ask, comp conversation notes.
```

**Everything derivable is derived, never stored:** `days_in_stage`, rollup
counts, time-to-offer. `history` is the record; the views read it.

**Each history entry carries two dates.** They answer different questions and
only one of them is editable:

| Field | Means | Set by | Editable |
|---|---|---|---|
| `occurred` | when the thing happened in the world | you, defaulting to today | **yes**, any time |
| `recorded` | when you told the board about it | the app, automatically | never |

Most of the time they're equal and the distinction is invisible — you move the
card the day the thing happens. They diverge when you're catching up: the
technical screen was the 22nd, you didn't touch the board until the 25th, so the
entry reads `occurred: 2026-09-22, recorded: 2026-09-25`. Correcting `occurred`
later, from the history timeline in card detail, is exactly the case this exists
for.

**`occurred` drives everything the board shows.** `days_in_stage` reads
`history[-1].occurred`, so a card you updated three days late still reads its true
age. `recorded` is never used in a view — it exists so the log stays an honest
account of what you knew and when, which is precisely the value it loses if you
can edit it. One soft number and one hard one; two soft numbers would be no
record at all.

**`occurred` cannot be later than `recorded`.** You can backdate, not
forward-date. A future `occurred` would be a scheduled event — "panel on the
30th" — and that is a due date, which §5.5 removed deliberately. If this
constraint ever chafes, the thing being asked for is a calendar, and that's a
non-goal (§1).

**`stage_since` was removed.** `history[-1].occurred` *is* the date the card
entered its current stage, and holding the same fact twice means hand-editing one
and forgetting the other — a silent wrong number on the card face, with nothing
to catch it.

**`stage` stays stored even though `history[-1].to` would give it.** That's a
deliberate exception: §3 leans on `grep -l "stage: technical" cards/*.yaml` as a
reason to use YAML at all, and deriving it would cost that. The rule of thumb is
that a field you'd grep for earns duplication and a date doesn't.

### 5.3 Stages

```
Board columns:  shortlist → applied → informational → technical → take-home → panel → offer
Archive:        archived   (+ a `reason`)
```

There is no `inbox` stage — unreviewed cards live in `inbox/` and appear only in
the Discovery view.

**`take-home` is its own column because it stalls differently.** Every other
stage is time spent waiting on *them* — a card sitting in `applied` or `panel` is
outside your control, and the day count is a fact about their process. A
take-home is the one stage where the ball is in your court, and folding it into
`technical` hides that behind a number that looks identical. Seven columns is at
the edge of what fits a browser comfortably; if it gets tight, collapsing the
archive lane (§6.2) buys the room back.

**There is one archive stage, not three.** An earlier draft split it into
`no-hire`, `dropped` and `expired`. They collapsed into `archived` with a
`reason` field, because the stage answers "am I still in this?" and the answer is
the same in all three cases. Why it ended is a detail about the card, not a
different place in the pipeline — and three lanes on the board is three things to
render, drag between and reason about for a distinction you'd read off the card
anyway.

`reason` is a dropdown, stored on the card next to `stage`:

| Value | Means |
|---|---|
| `passed` | you decided not to pursue it |
| `rejected` | they said no |
| `withdrew` | you pulled out of a live process |
| `expired` | the posting closed without a decision |
| `other` | anything else — say what in the note |

It's null unless `stage` is `archived`, and it's stored rather than derived for
the same reason `stage` is: `grep -l "reason: rejected" cards/*.yaml` answers a
question you'll actually ask.

**Archiving, for any reason, is permanent as far as discovery is concerned.** A
sweep never re-surfaces an archived card (FIND-JOBS.md Phase 3). The old draft
specified this only for `dropped` and was silent on the others; one lane makes it
uniform. The cost is that a role you archived as `expired` a year ago won't come
back when it reposts.

### 5.4 Criteria — `data/criteria.yaml`

Yours, not the repo's. `config/criteria.example.yaml` ships the same shape with
placeholder values.

```yaml
version: v1
titles: [Data Scientist, MLOps Engineer, ML Engineer]
title_aliases: [ML Platform Engineer, ML Infrastructure Engineer,
                Senior Software Engineer ML Systems]
level: {min: senior, target: lead}
location:
  accept: [remote-us, seattle-hybrid]
  reject: [onsite-only, relocation, state-restricted-remote, non-pacific-hours]
exclusions:
  - {id: employer, values: [...]}
  - {id: sector,   values: [...]}
  - {id: on-call,  rule: "reject roles built around an on-call rotation"}
watchlist:                        # polled directly via each company's ATS API
  - {company: "...", ats: greenhouse, token: "..."}
  - {company: "...", ats: lever,      token: "..."}
fit_rubric:
  axes: [content_match, level_match, location_match]
  tiers: {strong: "all three", good: "two of three", out: "fails a hard filter"}
  drop: "technical content that is a genuine reach is dropped, not ranked"
candor: "name the specific skill gap per role; do not soften"
```

Criteria govern *discovery* only — what to search for and what to screen out.
Nothing here configures the board. An earlier draft added `staleness_days`, a
per-stage threshold past which a card was flagged; see §5.5 for why it went.

### 5.5 Time is shown, not judged

**The card face shows `days_in_stage`. Nothing interprets it.**

That number is a fact about the file — how long this has sat where it is. It is
derived from `history[-1].occurred` and rendered as-is. A card reading `applied · 34
days` has told you everything the system knows; whether 34 days means *follow up*
or *they're just slow* or *let it go* is a judgment about that company, that
recruiter and how much you want the job, and the tool has none of those inputs.

**What was cut, and why.** Two earlier drafts of this section built progressively
more machinery on top of that number:

- A user-set `next_action.due` date per card. Dropped first: this process doesn't
  generate deadlines. Nobody assigns you one for following up on an application,
  and a self-imposed one is a reminder you invented and will resent.
- Per-stage `staleness_days` thresholds, a stale flag on cards past theirs, a
  `snoozed_until` field and Snooze button to silence it, an urgency sort ranking
  cards by how far over they were, and a needs-attention strip collecting them.

The thresholds were the problem. They were invented numbers — the draft admitted
it and promised to tune them later — and a flag driven by a guess is wrong often
enough that you learn to ignore it. A board of ignorable flags is worse than a
board with none, because it still *looks* authoritative. The rest of that
machinery existed only to service, silence and sort the flag.

Deleting the threshold keeps the whole signal and drops only the opinion about
it. `days_in_stage` is still on every card and still orders the columns (§5.6).
What's gone is `staleness_days`, `is_stale()`, `snoozed_until`, the snooze
endpoint and button, the urgency tiers, and the needs-attention strip.

**Stage moves still take an optional date, defaulting to today.** Apply Monday,
update the board Thursday, and an undated move makes the card read three days
younger than it is. Backdating is what keeps the number true, and the number is
now the only thing the board says about time — so it should be right. That's what
the `occurred` / `recorded` split in §5.2 is for: set `occurred` when you know the
real date, correct it later when you don't.

**If this turns out to be wrong**, you'll know how: you'll repeatedly notice you
let something sit too long, and you'll know the actual number of days for that
stage. Thresholds added then are earned rather than guessed, and nothing is
stored against them, so adding them later is a config change and a view change
with no migration.

### 5.6 Card order within a column

**No stored order and no manual override.** Within a column, cards sort **oldest
first** — longest `days_in_stage` at the top, ties broken on company name so the
sort is stable.

That is the entire rule, and it has the property a filing cabinet needs: it never
reshuffles. Oldest-first within a stage is just entry order into that stage, so a
card only moves when you move it. Open the board tomorrow and everything is where
you left it.

**`pinned` was cut.** It survived the §5.5 pass on the argument that it's an
ordering *you* express rather than one the tool infers — which is still true, and
still wasn't enough. With a handful of cards per column and an order that never
reshuffles, everything is already on screen and already where you left it; a pin
floats a card above a neighbour you can see anyway. If columns ever get long
enough that you lose track of one, that's the signal to bring it back.

**Manual reordering was considered and rejected.** With seven columns and a handful
of cards each, everything is on screen; drag-to-reorder earns its keep on a
forty-card board where sorting is how you cope with not seeing everything. It
also means the drag handler never has to tell a reorder from a move, which is
where most kanban drag bugs live (§6.2).

---

## 6. Code architecture

### 6.1 Core library

`src/` owns loading, validation, mutation and derivation. Both views are thin
adapters over it. This is what makes a third interface — a CLI, a static
renderer — cost a fraction of the first.

```python
# src/config.py
DATA_DIR: Path                              # <repo root>/data — a constant
def load_criteria(root: Path = DATA_DIR) -> Criteria

# src/models.py
@dataclass class Card: ...                  # both zones, parsed and validated
@dataclass class Discovery: ...
@dataclass class Pipeline: ...

# src/store.py — the only module that touches the filesystem
def load_inbox(root: Path = DATA_DIR) -> list[Card]
def load_cards(root: Path = DATA_DIR) -> list[Card]
def load(card_id: str, root: Path = DATA_DIR) -> Card
def save(card, expected_mtime, root=DATA_DIR) -> float   # atomic; raises on conflict
def review(card_id, interested, root=DATA_DIR) -> Card   # inbox/ -> cards/; seeds history

# src/pipeline.py — the only place stage changes
def move(card, to_stage, reason=None, note="", occurred=today) -> Card
def amend(card, index: int, occurred: date = None, note: str = None) -> Card

# src/views.py — everything derived
def days_in_stage(card: Card, today: date) -> int       # history[-1].occurred
def board(cards: list[Card]) -> dict[Stage, list[Card]] # columns, oldest first
def queue(cards: list[Card]) -> list[Card]              # inbox, sorted for review
```

`views.py` is four functions because §5.5 deleted the rest. Nothing in `src/`
takes `today` except `days_in_stage`, and nothing reads `criteria.yaml` at all —
criteria govern discovery, not the board.

**Any stage moves to any stage.** There is no transition table and no
`legal_moves()`. Applied straight to offer skips four columns and does happen;
moving a card backwards when you misfiled it is ordinary. A filing cabinet lets
you put a file in any drawer, and a rejected move is the tool overruling you
about your own process. `move()` appends to `history` and rewrites `stage` —
that's all it does.

**`history` is never empty.** `review()` writes the first entry when it promotes
a card out of `inbox/`. This is load-bearing now that `stage_since` is derived
(§5.2) — `days_in_stage` reads `history[-1].occurred`, so a card with no history
has no clock. Every card in `cards/` has at least one entry, by construction.
Worth a test.

**`history[-1].to` always equals `stage`**, because `move()` sets both. So
`days_in_stage` is well defined even when entries are recorded out of
chronological order — it asks "how long since the event that put me here", and
the last entry is always that event. Out-of-order `occurred` dates render an odd
timeline, which is visible and fixable, rather than a wrong day count, which
wouldn't be.

**A move to `archived` prompts for a reason and a note; every other move
doesn't.** Archiving is the one transition whose reasoning you lose immediately
and want back later — when the same role resurfaces under a new req two months
on, `history` is the only place that remembers you already looked at this and
why. Every other stage change explains itself: the stage *is* the news.

This applies wherever a card is archived — **Pass** in the review queue, or a
drag to the archive lane on the board. Both call `move(card, "archived", reason,
note)`.

**The note is always skippable** — one line, Enter accepts it empty. Review is
twenty decisions in a sitting and a mandatory field breaks that rhythm; a note
you were forced to type is worth less than the one you chose to. The `reason`
dropdown defaults to `passed` from the review queue and is unset elsewhere, so
archiving is never more than one keystroke when you have nothing to add.

`src/` knows nothing about HTTP, HTML, or the browser. **Every function that
touches disk takes `root`, defaulting to `DATA_DIR`** — that parameter is the
whole of the test seam, and the reason §2 needs no environment variable. Tests
pass a fixture directory; the app never passes anything.

`save()` writes to a temp file and `os.replace()`s it — atomic on POSIX, so a
crash mid-write can't leave a half-parsed card.

### 6.2 Two views, one app

Flask, one server, tabs in a shared nav. Not two apps — you'll flip between them,
and two processes to start is one too many.

**Discovery tab — a review queue, not a board.**

Dense and readable, because you're making twenty decisions in one sitting. A
table or list, one row per `inbox/` card, sorted by tier then comp, filterable by
location. Each row shows company, title, comp band, location, tier
badge, and the Why / Gap lines in full — the fit rationale is the thing you're
deciding on, so it doesn't get truncated behind a click.

Two actions per row, keyboard-bound: **Interested** → `cards/` at `shortlist`,
**Pass** → `cards/` at `archived`. Pass opens a one-line note prompt, skippable
with Enter (§6.1); Interested doesn't. No drag-and-drop; over twenty items a
keystroke beats a drag every time. An empty queue is the normal resting state and should
say so, not look broken.

**Board tab — the kanban.**

Seven columns, drag-and-drop between them, the archive lane collapsed below or
behind a toggle. Card face shows company, title, days-in-stage, and a badge when
`referral.status` is anything but `none` — a referral changes the odds enough to be worth seeing without
opening the card. Click opens detail: history timeline, contacts,
referral, notes, the original Why / Gap, link to the posting.

Drag-and-drop moves cards **between** columns only. There is no vertical
reordering, so the drop handler never has to distinguish a reorder from a move —
which is where most kanban drag bugs live.

There is no needs-attention strip, no flags and no badges beyond the referral
one. The board's job is to show you what you have; you read the columns and the
day counts and decide. See §5.5.

### 6.3 Routes

```
GET    /                        -> redirect to /board
GET    /board                   -> board view
GET    /discovery               -> review queue
GET    /api/cards               -> JSON, for client refresh
GET    /api/inbox               -> JSON queue
POST   /api/inbox/<id>/review    -> {interested: bool, note?} — the seam
PATCH  /api/cards/<id>/stage    -> {to, reason?, note, occurred?} — drag-drop
PATCH  /api/cards/<id>/history/<i> -> {occurred?, note?} — correct a past entry
PATCH  /api/cards/<id>          -> notes, contacts, referral
```

**Drag-and-drop:** HTML5 drag events, no library. On drop, optimistically move
the card in the DOM, `PATCH` the stage, snap back with a visible error on
failure. Never leave the DOM showing a state the file doesn't have.

**Concurrency:** one user, but a discovery session or hand-edit can change a file
underneath you. Every write sends the `mtime` read at load; the server refuses a
mismatched write and the client reloads that card. Ten lines, and it turns a
silent overwrite into a visible refresh.

**Binds to 127.0.0.1 only, no auth.** This reads recruiter names and live
negotiation notes off disk; it does not go on `0.0.0.0`.

### 6.4 `make init`

Creates `data/` and its subpaths and copies `criteria.example.yaml` to
`data/criteria.yaml` for editing. First run is one command.

**There is no `jobs` CLI and no console-script entry point.** Setup is four
`mkdir -p`s and a `cp` — a Makefile target, not an argument parser and a
packaging block. This is a repo you `cd` into and run `make dev` in, not a tool
you install. The cost is that commands only work from the repo directory, which
is where you'd be running them anyway.

If it ever *is* worth installing — someone else picks this up, or you want to run
a sweep from elsewhere — §6.1's core library is the thing that makes adding a CLI
cheap later. Nothing here forecloses it.

### 6.5 No static export

An earlier draft added `make render` — a self-contained read-only HTML board,
publishable for checking from a phone. Cut. The board is a thing you open on your
laptop, and §6.3 already declined to put this data on the network; rendering the
same recruiter names and comp notes into a file made to be hosted somewhere would
have contradicted that two sections later. A snapshot is also stale the moment
it's made, so keeping it current means regenerating and republishing on every
change — friction you'd stop paying inside a week.

The running app is the only interface. `make dev`, `127.0.0.1`, done.

---

## 7. Repo layout

```
kanban-jobs/
  README.md
  .gitignore
  pyproject.toml
  Makefile
  docs/
    conf.py                     # Sphinx config; myst-parser renders these .md files directly
    index.md
    FIND-JOBS.md                 # the procedure a search session follows
    design/
      ARCHITECTURE.md            # this document
  hooks/
    pre-commit                  # installed by `make init`; delegates to `make check-staged`
  config/
    criteria.example.yaml       # schema + placeholders, no personal values
    profile.example.md          # template + placeholders, no personal values
  src/
    __init__.py
    config.py                   # data-dir resolution
    models.py                   # dataclasses + schema validation
    store.py                    # the only filesystem writer
    pipeline.py                 # stage transitions
    views.py                    # derived state
  app/
    server.py                   # Flask
    static/board.js             # drag-drop
    static/discovery.js         # review keybindings
    static/card.js               # card-detail autosave
    static/app.css
    templates/
      base.html                 # shared nav
      board.html
      discovery.html
      card.html
  tests/
    fixtures/                   # invented cards, fictional companies
    test_pipeline.py
    test_views.py
    test_store.py
    test_boundary.py            # asserts discovery can't write cards/
    test_app.py
```

No `data/`. It isn't in the repo; `make init` creates it elsewhere.

The `Makefile` is the entry point for everything: `make init` (§6.4), `make dev`,
`make test`, `make check-clean` / `make check-staged` (§9), `make lint`, `make
typecheck`, and `make docs`. No `cli.py`, no `[project.scripts]` — see §6.4.

**Stack:** Python 3.11+, `pyyaml`, `jinja2`, `flask`, `pytest`, `ruff`, `mypy`,
`sphinx` + `myst-parser` + `furo`. No frontend build step — plain JS and CSS
served as static files. `make dev` starts it.

---

## 8. Discovery workflow

**`FIND-JOBS.md` is the full procedure**; it ships in the repo and is what a
session reads before starting. Summary:

### One job, run by hand

A sweep finds and screens new candidates, and writes `inbox/`. That is the whole
of discovery. It makes judgment calls the rubric can't fully specify, so it's a
Claude session — started deliberately, monthly-ish, never automated.

Nothing re-checks cards already in play. See §4 for why the health check and the
alert channel were cut.

A scheduled task is still fine as a *reminder* to run a sweep. It is the wrong
thing to run the sweep itself — the data is local, and a cloud session can't
reach it reliably.

### Sources

**ATS APIs first.** Greenhouse, Lever and Ashby publish per-company job boards as
public JSON — no auth, structured fields, more reliable than parsing HTML. This
is what the `watchlist` in `criteria.yaml` is polled through, and it's higher
yield than any keyword search. It also solves Ashby, whose postings are
JavaScript-rendered and unreadable through a normal fetch.

**Aggregator boards for breadth** — Built In, RemoteRocketship, hiddenjobs.dev,
startup.jobs, HN "Who is hiring". Ranked with their known weaknesses in
`FIND-JOBS.md`.

**No credentialed sources.** LinkedIn and Indeed are login-walled, and automated
access to a logged-in session violates their terms and risks the account. The
procedure explicitly instructs sessions not to accept credentials if offered. The
legitimate route for LinkedIn coverage is Claude in Chrome on your own machine,
driving your own authenticated browser with you present.

### Screening

**Hard filters before fetching.** Employer, sector, location eligibility and
level resolve on metadata the board already gave you. Fetching is the expensive
step; most candidates should die before it.

**Volume capped at ~25 per sweep** — not a technical limit, but the difference
between a queue you clear and one you avoid.

A card in `cards/` at stage `archived` is one you're not continuing with, for
whatever reason, and is never re-surfaced. That is the entire reason archived
candidates are kept rather than deleted.

---

## 9. Keeping data out of git

The data lives inside the repo (§2), so this section is load-bearing rather than
precautionary. The cost of getting it wrong is unrecoverable.

**`.gitignore`:**

```
data/
config/criteria.yaml
*.local.yaml
.env
```

**Pre-commit hook** — rejects any commit that stages a path under `data/` or
`config/criteria.yaml`, with a message saying why, via `make check-staged`. It
also catches the case where someone (you, in six months, in a hurry) drops a
real card into `tests/fixtures/`. That guard runs first and is not
skippable; the hook then also runs `make lint`, `make typecheck`, and `make
test`, so a broken commit is caught locally rather than in CI.

**`make init` installs the hook**, and fails if it can't. A hook that exists only
in the README isn't a mechanism, and hooks don't survive a fresh clone — so the
one command you run before anything else is the one that puts it in place.

**`make check-clean`** — greps the git index for tracked paths under `data/` and
exits non-zero. Cheap to run, and the thing to check before ever making the repo
public. Wire it into `make test`.

**Fixtures are invented, never scrubbed.** Scrubbing leaks — a "redacted" fixture
keeps the comp band, the city, the stage history. Write fictional companies.

**`test_boundary.py`.** After a simulated discovery run, assert `cards/` is
untouched. The two-writer rule is otherwise just a convention, and conventions
decay.

---

## 10. Open decisions

| # | Decision | Recommendation |
|---|---|---|
| 1 | Data outside repo, or gitignored inside? | **Inside, gitignored** — one folder to hold and back up; §9 becomes the mechanism |
| 2 | Take-home as its own column? | **Yes** — it's the one stage waiting on you, not them (§5.3) |
| 3 | Staleness thresholds | Cut — ship the raw day count, add thresholds only if real use shows the number (§5.5) |
| 4 | Static snapshot in scope? | **No** — cut; it contradicts §6.3 and goes stale (§6.5) |

---

## 11. Build order

- **M1 — Core + config.** `config.py`, `models.py`, `store.py`, `pipeline.py`,
  `views.py`, `make init`, `criteria.example.yaml`, invented fixtures, tests
  green including `test_boundary.py`. No UI. **This is the milestone that
  matters** — if the data model is wrong, everything after it is rework.
- **M2 — Discovery view.** The review queue, read-only first, then the review
  endpoint. Smaller than the board and it's the tab you need first: nothing
  reaches the board until review exists.
- **M3 — Read-only board.** Server-rendered columns, no writes. Proves the views.
- **M4 — Drag-and-drop.** Stage endpoint, optimistic UI, mtime conflict handling.
  The board becomes usable.
- **M5 — Card detail.** Notes, contacts, referral, history timeline with
  editable `occurred` dates and notes. **This is the last milestone** — the tool
  is finished here, not paused.

Then, separately: seed the data dir from `listings-seed.yaml` and start using it.

M2 before M3 is deliberate. Discovery is the smaller surface, it's the upstream
half of the flow, and building it first means the first cards on the board got
there the way every later card will.

---

## 12. Risks

**The two-writer rule is a convention, not a mechanism.** Nothing stops a
discovery session writing `cards/`. Mitigate by putting the rule at the top of
`FIND-JOBS.md` where a session reads it first, exposing no `store.py` function
that writes `cards/` from a discovery context, and keeping `test_boundary.py`
green.

**Link rot, unevenly.** Aggregator URLs (Built In, RemoteRocketship,
startup.jobs) die much faster than employer ATS URLs (Greenhouse, Ashby, Lever,
Workday). About half the seed entries point at aggregators because that's where
they surfaced. `url_kind` marks which; resolve each to its ATS URL on first
contact with the company.

**Optimistic UI that lies.** The classic drag-and-drop bug is the card that
visually moves while the write fails. Test the failure path before the happy one.

**Config drift between tool and data.** The tool's schema will change while your
`criteria.yaml` sits at the old shape. `version: v1` exists for this — validate
on load and fail loudly rather than silently ignoring fields the tool no longer
reads.

**Review fatigue.** Twenty cards in the queue is a pleasant review session; two
hundred is a chore you'll avoid, and an avoided queue means the board goes stale.
Keep discovery runs small and frequent rather than large and rare.

**Scope creep into a CRM.** Every field added to the pipeline zone is a field to
maintain by hand during the weeks when the search is busiest. The non-goals in §1
are load-bearing.

---

## Appendix: what already exists

**`listings-seed.yaml`** — 21 roles screened and verified 2026-09-06 against the
criteria above: 16 tracked, 5 screened out on location filters. **This is data,
not repo content.** Split it into `data/inbox/*.yaml` after `make init`
so your first review session has real cards, and don't commit it.

**`pipeline-prototype.html`** — a working single-file board: tier grouping,
filters, per-role status and notes, state persisted by republishing itself.
Roughly M3 plus a flat version of the pipeline zone. Read it for the render layer
and the card copy; discard it as an architecture, since it holds listings inline
in JavaScript, which is exactly the coupling this plan separates.
