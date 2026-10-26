from flask import Blueprint, jsonify, send_file
from services import report_service as rs
bp = Blueprint("report", __name__)

@bp.route("/api/dashboard")
def dash(): return jsonify(rs.dashboard())

@bp.route("/api/reports/<kind>/<fmt>")
def report(kind, fmt):
    if fmt not in ("xlsx", "pdf"): return jsonify({"error": "fmt must be xlsx or pdf"}), 400
    buf, mime, name = rs.export(kind, fmt)
    if buf is None: return jsonify({"error": "Unknown report"}), 404
    return send_file(buf, mimetype=mime, as_attachment=True, download_name=name)
