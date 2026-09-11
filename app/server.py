from __future__ import annotations

from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

from core import store, views
from core.config import DATA_DIR
from core.models import Card


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


def _card_json(card: Card) -> dict:
    return {
        "id": card.id,
        "company": card.company,
        "title": card.title,
        "team": card.team,
        "tier": card.assessment.tier,
        "why": card.assessment.why,
        "gap": card.assessment.gap,
        "location": {"mode": card.location.mode, "scope": card.location.scope},
        "comp": _comp_text(card.comp),
        "url": card.url,
        "stage": card.stage,
    }


def create_app(root: Path = DATA_DIR) -> Flask:
    app = Flask(__name__)
    app.config["DATA_ROOT"] = root
    app.jinja_env.filters["comp_text"] = _comp_text

    def data_root() -> Path:
        return app.config["DATA_ROOT"]

    @app.get("/")
    def index():
        # -> /board once M3 exists
        return redirect(url_for("discovery"))

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

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
