import json
from datetime import datetime
from db import query, execute

def find_intern(name):
    return query("SELECT * FROM interns WHERE name LIKE %s", (f"%{name.strip()}%",))

def conflict(date, time, mentor, link, intern_id):
    return query("""SELECT i.name, r.mentor, r.meeting_link FROM reviews r JOIN interns i ON i.id=r.intern_id
        WHERE r.review_date=%s AND r.review_time=%s AND r.status='pending' AND r.intern_id<>%s
        AND (r.mentor=%s OR (r.meeting_link<>'' AND r.meeting_link=%s))""",
        (date, time, intern_id, mentor, link), one=True)

def request(intern_id, date, time, link=None, followup=False):
    try:
        datetime.strptime(date, "%Y-%m-%d")
        time = datetime.strptime(time, "%H:%M:%S" if time.count(":") == 2 else "%H:%M").strftime("%H:%M:%S")
    except ValueError:
        return {"ok": False, "message": "Invalid date/time. Use YYYY-MM-DD and HH:MM."}
    intern = query("SELECT * FROM interns WHERE id=%s", (intern_id,), one=True)
    if not intern: return {"ok": False, "message": "Intern not found."}
    last = query("SELECT meeting_link FROM reviews WHERE intern_id=%s ORDER BY id DESC LIMIT 1", (intern_id,), one=True)
    link = link or (last["meeting_link"] if last else "")
    c = conflict(date, time, intern["mentor"], link, intern_id)
    if c:
        return {"ok": False, "message": f"Conflict: {c['name']} already has a review at {date} {time[:5]} "
                f"with the same mentor/link. Nothing was changed. Pick another slot."}
    payload = dict(intern_id=intern_id, date=date, time=time, link=link, followup=followup, name=intern["name"])
    pid = execute("INSERT INTO pending_actions (action_type,payload) VALUES ('schedule',%s)", (json.dumps(payload),))
    kind = "follow-up review" if followup else "review"
    return {"ok": True, "pending_id": pid,
            "message": f"Schedule {kind} for {intern['name']} on {date} at {time[:5]}? Say yes to confirm or no to cancel."}

def create_pending(action_type, payload):
    return execute("INSERT INTO pending_actions (action_type,payload) VALUES (%s,%s)", (action_type, json.dumps(payload)))

def latest_awaiting():
    return query("SELECT * FROM pending_actions WHERE status='awaiting' ORDER BY id DESC LIMIT 1", one=True)

def list_pending():
    rows = query("SELECT * FROM pending_actions WHERE status='awaiting' ORDER BY id DESC")
    for r in rows:
        if isinstance(r["payload"], str): r["payload"] = json.loads(r["payload"])
    return rows

def execute_action(action_id):
    a = query("SELECT * FROM pending_actions WHERE id=%s AND status='awaiting'", (action_id,), one=True)
    if not a: return "No pending action found."
    p = json.loads(a["payload"]) if isinstance(a["payload"], str) else a["payload"]
    if a["action_type"] == "schedule":
        intern = query("SELECT * FROM interns WHERE id=%s", (p["intern_id"],), one=True)
        if conflict(p["date"], p["time"], intern["mentor"], p["link"], p["intern_id"]):
            cancel_action(action_id); return "Slot was taken meanwhile. Action cancelled, nothing changed."
        if not p["followup"]:
            execute("UPDATE reviews SET status='rescheduled' WHERE intern_id=%s AND status='pending' AND is_followup=0", (p["intern_id"],))
        execute("INSERT INTO reviews (intern_id,review_date,review_time,meeting_link,mentor,is_followup) VALUES (%s,%s,%s,%s,%s,%s)",
                (p["intern_id"], p["date"], p["time"], p["link"], intern["mentor"], p["followup"]))
        msg = f"Done. Review for {p['name']} scheduled on {p['date']} at {p['time'][:5]}."
    elif a["action_type"] == "send_emails":
        from services import email_service
        r = email_service.send_bulk(p["kind"], p["review_ids"])
        demo_tag = " (Demo mode — set Gmail in .env for real inbox)" if r.get("demo") else ""
        msg = f"Emails processed: {r['sent']} sent{demo_tag}, {r['failed']} failed."
    elif a["action_type"] == "send_single_email":
        from services import email_service
        r = email_service.send_single(p)
        if r.get("error"):
            msg = f"Email delivery failed: {r['error']}"
        elif r.get("demo"):
            msg = f"Done! Email recorded as sent for {p['name']} ({r.get('to')}). Status: Sent (Demo mode — see Emails tab, or add Gmail App Password in .env for real inbox delivery)."
        else:
            msg = f"Done! Live email sent to {p['name']} ({r.get('to')})."
    elif a["action_type"] == "broadcast":
        from services import email_service
        r = email_service.send_broadcast(p.get("subject", ""), p.get("body", ""), p.get("intern_ids", []))
        demo_tag = " (Demo mode — set Gmail in .env for real inbox)" if r.get("demo") else ""
        msg = f"Broadcast done: {r['sent']} sent{demo_tag}, {r['failed']} failed."
    else: msg = "Unknown action."
    execute("UPDATE pending_actions SET status='executed' WHERE id=%s", (action_id,))
    return msg

def cancel_action(action_id):
    execute("UPDATE pending_actions SET status='cancelled' WHERE id=%s", (action_id,))
    return "Cancelled. Nothing was changed."

def list_reviews(today=False):
    sql = """SELECT r.id,i.name,i.email,i.task,r.mentor,r.review_date,r.review_time,r.meeting_link,r.status,r.is_followup
             FROM reviews r JOIN interns i ON i.id=r.intern_id"""
    if today: return query(sql + " WHERE r.review_date=CURDATE() ORDER BY r.review_time")
    return query(sql + " ORDER BY r.review_date, r.review_time")

def set_status(review_id, status):
    if status not in ("pending", "completed", "missed", "rescheduled"): return False
    execute("UPDATE reviews SET status=%s WHERE id=%s", (status, review_id)); return True

def flag_overdue():
    return execute("UPDATE reviews SET status='missed' WHERE status='pending' AND TIMESTAMP(review_date,review_time) < NOW()", rc=True)
