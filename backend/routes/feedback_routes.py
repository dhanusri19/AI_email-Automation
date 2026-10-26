from flask import Blueprint, request, jsonify
from services import feedback_service as fs
bp = Blueprint("feedback", __name__)

@bp.route("/api/feedback", methods=["GET"])
def lst(): return jsonify(fs.list_all())

@bp.route("/api/feedback", methods=["POST"])
def add():
    d = request.json or {}
    r = fs.add(d.get("review_id"), d.get("mentor_name", ""), d.get("rating"), d.get("comments", ""), d.get("outcome"))
    return jsonify(r), (200 if r["ok"] else 400)

@bp.route("/api/followups/suggest")
def suggest(): return jsonify(fs.suggest_followups())
