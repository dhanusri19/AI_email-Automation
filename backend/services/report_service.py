import io
import pandas as pd
from db import query

def dashboard():
    rv = {r["status"]: r["c"] for r in query("SELECT status,COUNT(*) c FROM reviews GROUP BY status")}
    em = {r["status"]: r["c"] for r in query("SELECT status,COUNT(*) c FROM email_logs GROUP BY status")}
    return {"interns": query("SELECT COUNT(*) c FROM interns", one=True)["c"],
            "today": query("SELECT COUNT(*) c FROM reviews WHERE review_date=CURDATE()", one=True)["c"],
            "pending": rv.get("pending", 0), "completed": rv.get("completed", 0),
            "missed": rv.get("missed", 0), "rescheduled": rv.get("rescheduled", 0),
            "emails_sent": em.get("sent", 0), "emails_failed": em.get("failed", 0)}

def _data(kind):
    if kind == "progress":
        return query("""SELECT i.name,i.email,i.task,i.mentor,r.status AS review_status,r.review_date,
            (SELECT outcome FROM feedback f WHERE f.review_id=r.id ORDER BY f.id DESC LIMIT 1) AS outcome,
            (SELECT rating FROM feedback f WHERE f.review_id=r.id ORDER BY f.id DESC LIMIT 1) AS rating
            FROM interns i LEFT JOIN reviews r ON r.id=(SELECT MAX(id) FROM reviews WHERE intern_id=i.id) ORDER BY i.id""")
    if kind == "reviews":
        return query("""SELECT i.name,r.mentor,r.review_date,r.review_time,r.status,r.is_followup
                        FROM reviews r JOIN interns i ON i.id=r.intern_id ORDER BY r.review_date,r.review_time""")
    if kind == "emails":
        return query("""SELECT i.name,i.email,e.type,e.status,e.error,e.sent_at FROM email_logs e
                        LEFT JOIN interns i ON i.id=e.intern_id ORDER BY e.id DESC""")
    return None

def export(kind, fmt):
    rows = _data(kind)
    if rows is None: return None, None, None
    df = pd.DataFrame(rows).fillna("")
    buf = io.BytesIO()
    if fmt == "xlsx":
        df.to_excel(buf, index=False, sheet_name=kind)
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        data = [list(df.columns)] + [[str(x)[:28] for x in r] for r in df.values.tolist()]
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.lightblue), ("GRID", (0, 0), (-1, -1), .3, colors.grey),
                               ("FONTSIZE", (0, 0), (-1, -1), 6)]))
        SimpleDocTemplate(buf, pagesize=landscape(A4)).build([Paragraph(f"{kind.title()} Report", getSampleStyleSheet()["Title"]), t])
        mime = "application/pdf"
    buf.seek(0)
    return buf, mime, f"{kind}_report.{fmt}"
