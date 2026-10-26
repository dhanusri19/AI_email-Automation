from flask import Blueprint, request, jsonify
from services import chatbot_service as cb
bp = Blueprint("chat", __name__)

@bp.route("/api/chat", methods=["POST"])
def chat():
    return jsonify(cb.process((request.json or {}).get("message", "")))
