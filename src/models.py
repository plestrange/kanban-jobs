from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

STAGES = [
    "shortlist",
    "applied",
    "informational",
    "technical",
    "take-home",
    "panel",
    "offer",
    "archived",
]

TIERS = ["strong", "good", "out"]

ARCHIVE_REASONS = ["passed", "rejected", "withdrew", "expired", "other"]


def _parse_date(value) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


@dataclass
class Location:
    mode: str
    scope: str
    eligible: bool = True


@dataclass
class Comp:
    min: int | None = None
    max: int | None = None
    currency: str = "USD"
    source: str = "none"


@dataclass
class Discovered:
    date: date
    via: str
    rubric: str


@dataclass
class Assessment:
    tier: str | None
    why: str
    gap: str


@dataclass
class HistoryEntry:
    occurred: date
    recorded: date
    to: str
    note: str = ""


@dataclass
class Contact:
    name: str
    role: str = ""
    note: str = ""


@dataclass
class Referral:
    status: str = "none"
    via: str = ""
    checked: date | None = None


@dataclass
class Listing:
    # search zone — written by job search sweeps, frozen at promotion
    id: str
    req_id: str | None
    company: str
    title: str
    team: str | None
    location: Location
    comp: Comp
    url: str
    url_kind: str
    discovered: Discovered
    assessment: Assessment
    company_summary: str = ""  # one line: what the company does, at a glance

    # pipeline zone — written by the app, yours alone
    stage: str | None = None  # None while the listing still lives in listings/
    reason: str | None = None
    history: list[HistoryEntry] = field(default_factory=list)
    contacts: list[Contact] = field(default_factory=list)
    referral: Referral = field(default_factory=Referral)
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> Listing:
        listing_id = data["id"]
        loc = data.get("location") or {}
        comp = data.get("comp") or {}
        disc = data.get("discovered") or {}
        assess = data.get("assessment") or {}
        ref = data.get("referral") or {}

        stage = data.get("stage")
        if stage is not None and stage not in STAGES:
            raise ValueError(f"{listing_id}: unknown stage {stage!r}")

        reason = data.get("reason")
        if reason is not None and reason not in ARCHIVE_REASONS:
            raise ValueError(f"{listing_id}: unknown reason {reason!r}")
        if stage == "archived" and reason is None:
            raise ValueError(f"{listing_id}: archived listing is missing a reason")

        tier = assess.get("tier")
        if tier is not None and tier not in TIERS:
            raise ValueError(f"{listing_id}: unknown tier {tier!r}")

        history = [
            HistoryEntry(
                occurred=_parse_date(h["occurred"]),
                recorded=_parse_date(h["recorded"]),
                to=h["to"],
                note=h.get("note", ""),
            )
            for h in (data.get("history") or [])
        ]
        contacts = [
            Contact(name=c["name"], role=c.get("role", ""), note=c.get("note", ""))
            for c in (data.get("contacts") or [])
        ]

        return cls(
            id=listing_id,
            req_id=data.get("req_id"),
            company=data["company"],
            title=data["title"],
            team=data.get("team"),
            location=Location(
                mode=loc.get("mode", ""),
                scope=loc.get("scope", ""),
                eligible=loc.get("eligible", True),
            ),
            comp=Comp(
                min=comp.get("min"),
                max=comp.get("max"),
                currency=comp.get("currency", "USD"),
                source=comp.get("source", "none"),
            ),
            url=data.get("url", ""),
            url_kind=data.get("url_kind", "ats"),
            discovered=Discovered(
                date=_parse_date(disc["date"]),
                via=disc.get("via", ""),
                rubric=disc.get("rubric", ""),
            ),
            assessment=Assessment(tier=tier, why=assess.get("why", ""), gap=assess.get("gap", "")),
            company_summary=data.get("company_summary", ""),
            stage=stage,
            reason=reason,
            history=history,
            contacts=contacts,
            referral=Referral(
                status=ref.get("status", "none"),
                via=ref.get("via", ""),
                checked=_parse_date(ref["checked"]) if ref.get("checked") else None,
            ),
            notes=data.get("notes", ""),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "req_id": self.req_id,
            "company": self.company,
            "title": self.title,
            "team": self.team,
            "location": {
                "mode": self.location.mode,
                "scope": self.location.scope,
                "eligible": self.location.eligible,
            },
            "comp": {
                "min": self.comp.min,
                "max": self.comp.max,
                "currency": self.comp.currency,
                "source": self.comp.source,
            },
            "url": self.url,
            "url_kind": self.url_kind,
            "discovered": {
                "date": self.discovered.date,
                "via": self.discovered.via,
                "rubric": self.discovered.rubric,
            },
            "assessment": {
                "tier": self.assessment.tier,
                "why": self.assessment.why,
                "gap": self.assessment.gap,
            },
            "company_summary": self.company_summary,
            "stage": self.stage,
            "reason": self.reason,
            "history": [
                {"occurred": h.occurred, "recorded": h.recorded, "to": h.to, "note": h.note}
                for h in self.history
            ],
            "contacts": [{"name": c.name, "role": c.role, "note": c.note} for c in self.contacts],
            "referral": {
                "status": self.referral.status,
                "via": self.referral.via,
                "checked": self.referral.checked,
            },
            "notes": self.notes,
        }
