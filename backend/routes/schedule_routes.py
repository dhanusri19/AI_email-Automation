from flask import Blueprint, request, jsonify
from services import schedule_service as ss
bp = Blueprint("schedule", __name__)

@bp.route("/api/reviews")
def reviews(): return jsonify(ss.list_reviews())

@bp.route("/api/reviews/today")
def today(): return jsonify(ss.list_reviews(today=True))

@bp.route("/api/reviews/<int:rid>/status", methods=["POST"])
def status(rid):
    ok = ss.set_status(rid, (request.json or {}).get("status"))
    return jsonify({"ok": ok}), (200 if ok else 400)

@bp.route("/api/reviews/flag-overdue", methods=["POST"])
def overdue(): return jsonify({"flagged": ss.flag_overdue()})

@bp.route("/api/schedule/request", methods=["POST"])
def sched():
    d = request.json or {}
    return jsonify(ss.request(d.get("intern_id"), d.get("date", ""), d.get("time", ""), d.get("link"), bool(d.get("followup"))))

@bp.route("/api/pending")
def pending(): return jsonify(ss.list_pending())

@bp.route("/api/pending/<int:pid>/confirm", methods=["POST"])
def confirm(pid): return jsonify({"message": ss.execute_action(pid)})

@bp.route("/api/pending/<int:pid>/cancel", methods=["POST"])
def cancel(pid): return jsonify({"message": ss.cancel_action(pid)})
