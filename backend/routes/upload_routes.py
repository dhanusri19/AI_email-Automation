from flask import Blueprint, request, jsonify
from services import excel_service as ex
bp = Blueprint("upload", __name__)

@bp.route("/api/upload", methods=["POST"])
def upload():
    f = request.files.get("file")
    sheet_name = request.form.get("sheet_name")
    if not f or not f.filename.lower().endswith((".xlsx", ".xls")):
        return jsonify({"error": "Please upload an .xlsx or .xls file"}), 400
    valid, errors, total, analysis = ex.validate(f, sheet_name=sheet_name)
    if valid:
        ex.save(valid, f.filename, total, errors)
    return jsonify({
        "total": total,
        "saved": len(valid),
        "error_count": len(errors),
        "errors": errors,
        "sheet_analyzed": analysis.get("sheet_analyzed", ""),
        "available_sheets": analysis.get("available_sheets", []),
        "analysis": analysis,
    })

@bp.route("/api/interns")
def interns():
    return jsonify(ex.list_interns())
