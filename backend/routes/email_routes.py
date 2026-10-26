from flask import Blueprint, request, jsonify
from services import email_service as es
bp = Blueprint("email", __name__)

@bp.route("/api/email/preview")
def preview(): return jsonify(es.preview(request.args.get("kind", "review")))

@bp.route("/api/email/prepare", methods=["POST"])
def prepare(): return jsonify(es.prepare((request.json or {}).get("kind", "review")))

@bp.route("/api/email/broadcast/prepare", methods=["POST"])
def prepare_broadcast():
    b = request.json or {}
    return jsonify(es.prepare_broadcast(b.get("subject", ""), b.get("body", "")))

@bp.route("/api/email/logs")
def logs(): return jsonify(es.logs())
