from __future__ import annotations

from datetime import date
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

from src import pipeline, store, views
from src.config import DATA_DIR
from src.models import ARCHIVE_REASONS, STAGES, Card, Contact, Referral

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


def _card_json(card: Card, mtime: float | None = None) -> dict:
    data: dict[str, object] = {
        "id": card.id,
        "company": card.company,
        "company_summary": card.company_summary,
        "title": card.title,
        "team": card.team,
        "tier": card.assessment.tier,
        "why": card.assessment.why,
        "gap": card.assessment.gap,
        "location": {"mode": card.location.mode, "scope": card.location.scope},
        "comp": _comp_text(card.comp),
        "url": card.url,
        "stage": card.stage,
        "reason": card.reason,
        "note": card.history[-1].note if card.history else "",
    }
    if mtime is not None:
        data["mtime"] = mtime
    return data


def _card_detail_json(card: Card, mtime: float) -> dict:
    return {
        "id": card.id,
        "stage": card.stage,
        "reason": card.reason,
        "notes": card.notes,
        "contacts": [{"name": c.name, "role": c.role, "note": c.note} for c in card.contacts],
        "referral": {
            "status": card.referral.status,
            "via": card.referral.via,
            "checked": card.referral.checked.isoformat() if card.referral.checked else None,
        },
        "history": [
            {
                "index": i,
                "occurred": h.occurred.isoformat(),
                "recorded": h.recorded.isoformat(),
                "to": h.to,
                "note": h.note,
            }
            for i, h in enumerate(card.history)
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
        return redirect(url_for("board"))

    @app.get("/board")
    def board():
        cards = store.load_cards(root=data_root())
        columns = views.board(cards)
        archived = columns.pop("archived")
        mtimes = {c.id: store.mtime(c.id, root=data_root()) for c in cards}
        return render_template(
            "board.html",
            active="board",
            board_stages=BOARD_STAGES,
            columns=columns,
            archived=archived,
            today=date.today(),
            mtimes=mtimes,
            archive_reasons=ARCHIVE_REASONS,
        )

    @app.get("/cards/<card_id>")
    def card_detail(card_id):
        try:
            card = store.load(card_id, root=data_root())
        except FileNotFoundError:
            abort(404)
        if card.stage is None:
            abort(404)
        mtime = store.mtime(card_id, root=data_root())
        return render_template(
            "card.html",
            active="board",
            card=card,
            today=date.today(),
            mtime=mtime,
            referral_statuses=REFERRAL_STATUSES,
        )

    @app.get("/discovery")
    def discovery():
        cards = views.queue(store.load_inbox(root=data_root()))
        return render_template("discovery.html", cards=cards, active="discovery")

    @app.get("/api/inbox")
    def api_inbox():
        cards = views.queue(store.load_inbox(root=data_root()))
        return jsonify([_card_json(c) for c in cards])

    @app.post("/api/inbox/<card_id>/review")
    def api_review(card_id):
        payload = request.get_json(silent=True) or {}
        interested = bool(payload.get("interested"))
        note = (payload.get("note") or "").strip()
        try:
            card = store.review(card_id, interested=interested, note=note, root=data_root())
        except FileNotFoundError:
            abort(404)
        return jsonify(_card_json(card))

    @app.patch("/api/cards/<card_id>/stage")
    def api_move_stage(card_id):
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
            card = store.load(card_id, root=data_root())
        except FileNotFoundError:
            abort(404)

        try:
            pipeline.move(card, to_stage, reason=reason, note=note, occurred=occurred)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        try:
            new_mtime = store.save(card, payload.get("mtime"), root=data_root())
        except store.ConflictError:
            current = store.load(card_id, root=data_root())
            current_mtime = store.mtime(card_id, root=data_root())
            return jsonify({"error": "conflict", "card": _card_json(current, current_mtime)}), 409

        return jsonify(_card_json(card, new_mtime))

    @app.patch("/api/cards/<card_id>")
    def api_update_card(card_id):
        payload = request.get_json(silent=True) or {}
        try:
            card = store.load(card_id, root=data_root())
        except FileNotFoundError:
            abort(404)

        if "notes" in payload:
            card.notes = payload["notes"] or ""

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
            card.referral = Referral(status=status, via=ref.get("via", ""), checked=checked)

        if "contacts" in payload:
            card.contacts = [
                Contact(name=c["name"], role=c.get("role", ""), note=c.get("note", ""))
                for c in (payload["contacts"] or [])
                if (c.get("name") or "").strip()
            ]

        try:
            new_mtime = store.save(card, payload.get("mtime"), root=data_root())
        except store.ConflictError:
            current = store.load(card_id, root=data_root())
            current_mtime = store.mtime(card_id, root=data_root())
            return jsonify(
                {"error": "conflict", "card": _card_detail_json(current, current_mtime)}
            ), 409

        return jsonify(_card_detail_json(card, new_mtime))

    @app.patch("/api/cards/<card_id>/history/<int:index>")
    def api_amend_history(card_id, index):
        payload = request.get_json(silent=True) or {}
        try:
            card = store.load(card_id, root=data_root())
        except FileNotFoundError:
            abort(404)

        if index < 0 or index >= len(card.history):
            abort(404)

        occurred_raw = payload.get("occurred")
        try:
            occurred = date.fromisoformat(occurred_raw) if occurred_raw else None
        except ValueError:
            abort(400)

        try:
            pipeline.amend(card, index, occurred=occurred, note=payload.get("note"))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        try:
            new_mtime = store.save(card, payload.get("mtime"), root=data_root())
        except store.ConflictError:
            current = store.load(card_id, root=data_root())
            current_mtime = store.mtime(card_id, root=data_root())
            return jsonify(
                {"error": "conflict", "card": _card_detail_json(current, current_mtime)}
            ), 409

        return jsonify(_card_detail_json(card, new_mtime))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
