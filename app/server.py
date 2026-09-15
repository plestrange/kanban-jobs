from __future__ import annotations

from datetime import date
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

from src import pipeline, store, views
from src.config import DATA_DIR
from src.models import ARCHIVE_REASONS, STAGES, Contact, Listing, Referral

BOARD_STAGES = [s for s in STAGES if s != "archived"]
REFERRAL_STATUSES = ["none", "possible", "requested", "submitted"]


def _comp_text(comp) -> str:
    if comp.source != "posted":
        return "not posted"
    if comp.min and comp.max:
        return f"${comp.min // 1000}k–${comp.max // 1000}k"
    if comp.max:
        return f"up to ${comp.max // 1000}k"
    if comp.min:
        return f"${comp.min // 1000}k+"
    return "—"


def _listing_json(listing: Listing, mtime: float | None = None) -> dict:
    data: dict[str, object] = {
        "id": listing.id,
        "company": listing.company,
        "company_summary": listing.company_summary,
        "title": listing.title,
        "team": listing.team,
        "tier": listing.assessment.tier,
        "why": listing.assessment.why,
        "gap": listing.assessment.gap,
        "location": {"mode": listing.location.mode, "scope": listing.location.scope},
        "comp": _comp_text(listing.comp),
        "url": listing.url,
        "stage": listing.stage,
        "reason": listing.reason,
        "note": listing.history[-1].note if listing.history else "",
    }
    if mtime is not None:
        data["mtime"] = mtime
    return data


def _listing_detail_json(listing: Listing, mtime: float) -> dict:
    return {
        "id": listing.id,
        "stage": listing.stage,
        "reason": listing.reason,
        "notes": listing.notes,
        "contacts": [
            {"name": c.name, "role": c.role, "note": c.note} for c in listing.contacts
        ],
        "referral": {
            "status": listing.referral.status,
            "via": listing.referral.via,
            "checked": listing.referral.checked.isoformat() if listing.referral.checked else None,
        },
        "history": [
            {
                "index": i,
                "occurred": h.occurred.isoformat(),
                "recorded": h.recorded.isoformat(),
                "to": h.to,
                "note": h.note,
            }
            for i, h in enumerate(listing.history)
        ],
        "mtime": mtime,
    }


def create_app(root: Path = DATA_DIR) -> Flask:
    app = Flask(__name__)
    app.config["DATA_ROOT"] = root
    app.jinja_env.filters["comp_text"] = _comp_text
    app.jinja_env.filters["days_in_stage"] = views.days_in_stage

    def data_root() -> Path:
        return app.config["DATA_ROOT"]

    @app.get("/")
    def index():
        return redirect(url_for("interview_board"))

    @app.get("/interview-board")
    def interview_board():
        listings = store.load_interview_board(root=data_root())
        columns = views.interview_board(listings)
        archived = columns.pop("archived")
        mtimes = {c.id: store.mtime(c.id, root=data_root()) for c in listings}
        return render_template(
            "interview-board.html",
            active="interview-board",
            board_stages=BOARD_STAGES,
            columns=columns,
            archived=archived,
            today=date.today(),
            mtimes=mtimes,
            archive_reasons=ARCHIVE_REASONS,
        )

    @app.get("/interview-board/<listing_id>")
    def listing_detail(listing_id):
        try:
            listing = store.load(listing_id, root=data_root())
        except FileNotFoundError:
            abort(404)
        if listing.stage is None:
            abort(404)
        mtime = store.mtime(listing_id, root=data_root())
        return render_template(
            "listing.html",
            active="interview-board",
            listing=listing,
            today=date.today(),
            mtime=mtime,
            referral_statuses=REFERRAL_STATUSES,
        )

    @app.get("/listings")
    def listings():
        queued = views.queue(store.load_listings(root=data_root()))
        return render_template("listings.html", listings=queued, active="listings")

    @app.get("/api/listings")
    def api_listings():
        queued = views.queue(store.load_listings(root=data_root()))
        return jsonify([_listing_json(c) for c in queued])

    @app.post("/api/listings/<listing_id>/review")
    def api_review(listing_id):
        payload = request.get_json(silent=True) or {}
        interested = bool(payload.get("interested"))
        note = (payload.get("note") or "").strip()
        try:
            listing = store.review(listing_id, interested=interested, note=note, root=data_root())
        except FileNotFoundError:
            abort(404)
        return jsonify(_listing_json(listing))

    @app.patch("/api/interview-board/<listing_id>/stage")
    def api_move_stage(listing_id):
        payload = request.get_json(silent=True) or {}

        to_stage = payload.get("to")
        if to_stage not in STAGES:
            abort(400)

        reason = payload.get("reason") if to_stage == "archived" else None
        if to_stage == "archived" and reason not in ARCHIVE_REASONS:
            abort(400)

        note = (payload.get("note") or "").strip()

        occurred_raw = payload.get("occurred")
        try:
            occurred = date.fromisoformat(occurred_raw) if occurred_raw else None
        except ValueError:
            abort(400)

        try:
            listing = store.load(listing_id, root=data_root())
        except FileNotFoundError:
            abort(404)

        try:
            pipeline.move(listing, to_stage, reason=reason, note=note, occurred=occurred)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        try:
            new_mtime = store.save(listing, payload.get("mtime"), root=data_root())
        except store.ConflictError:
            current = store.load(listing_id, root=data_root())
            current_mtime = store.mtime(listing_id, root=data_root())
            return jsonify(
                {"error": "conflict", "listing": _listing_json(current, current_mtime)}
            ), 409

        return jsonify(_listing_json(listing, new_mtime))

    @app.patch("/api/interview-board/<listing_id>")
    def api_update_listing(listing_id):
        payload = request.get_json(silent=True) or {}
        try:
            listing = store.load(listing_id, root=data_root())
        except FileNotFoundError:
            abort(404)

        if "notes" in payload:
            listing.notes = payload["notes"] or ""

        if "referral" in payload:
            ref = payload["referral"] or {}
            status = ref.get("status", "none")
            if status not in REFERRAL_STATUSES:
                abort(400)
            checked_raw = ref.get("checked")
            try:
                checked = date.fromisoformat(checked_raw) if checked_raw else None
            except ValueError:
                abort(400)
            listing.referral = Referral(status=status, via=ref.get("via", ""), checked=checked)

        if "contacts" in payload:
            listing.contacts = [
                Contact(name=c["name"], role=c.get("role", ""), note=c.get("note", ""))
                for c in (payload["contacts"] or [])
                if (c.get("name") or "").strip()
            ]

        try:
            new_mtime = store.save(listing, payload.get("mtime"), root=data_root())
        except store.ConflictError:
            current = store.load(listing_id, root=data_root())
            current_mtime = store.mtime(listing_id, root=data_root())
            return jsonify(
                {"error": "conflict", "listing": _listing_detail_json(current, current_mtime)}
            ), 409

        return jsonify(_listing_detail_json(listing, new_mtime))

    @app.patch("/api/interview-board/<listing_id>/history/<int:index>")
    def api_amend_history(listing_id, index):
        payload = request.get_json(silent=True) or {}
        try:
            listing = store.load(listing_id, root=data_root())
        except FileNotFoundError:
            abort(404)

        if index < 0 or index >= len(listing.history):
            abort(404)

        occurred_raw = payload.get("occurred")
        try:
            occurred = date.fromisoformat(occurred_raw) if occurred_raw else None
        except ValueError:
            abort(400)

        try:
            pipeline.amend(listing, index, occurred=occurred, note=payload.get("note"))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        try:
            new_mtime = store.save(listing, payload.get("mtime"), root=data_root())
        except store.ConflictError:
            current = store.load(listing_id, root=data_root())
            current_mtime = store.mtime(listing_id, root=data_root())
            return jsonify(
                {"error": "conflict", "listing": _listing_detail_json(current, current_mtime)}
            ), 409

        return jsonify(_listing_detail_json(listing, new_mtime))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
