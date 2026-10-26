import html
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import Config
from db import query, execute
import services.schedule_service as ss

def _clean_err(err):
    if not err: return None
    s = str(err)
    if Config.SMTP_PASSWORD and Config.SMTP_PASSWORD in s:
        s = s.replace(Config.SMTP_PASSWORD, "******")
    return s

def _is_dummy_smtp():
    user = (Config.SMTP_USER or "").strip().lower()
    pw = (Config.SMTP_PASSWORD or "").strip()
    return not user or user == "your_email@gmail.com" or not pw or pw == "your_gmail_app_password"

def render(kind, r):
    if kind == "followup":
        subj = "Follow-up Review Meeting"
        body = (f"Hi {r['name']},\n\nBased on your last review, a follow-up meeting is scheduled.\n\nDate: {r['review_date']}\n"
                f"Time: {r['review_time'][:5]}\nLink: {r['meeting_link']}\n\nPlease prepare an update on: {r['task']}\n\nRegards,\nHR Team")
    else:
        subj = "Internship Review Meeting Scheduled"
        body = (f"Hi {r['name']},\n\nYour internship review meeting is scheduled.\n\nDate: {r['review_date']}\n"
                f"Time: {r['review_time'][:5]}\nLink: {r['meeting_link']}\n\nTask under review: {r['task']}\n\nRegards,\nHR Team")
    return subj, body

def _targets(kind, review_ids=None):
    fu = 1 if kind == "followup" else 0
    sql = """SELECT r.id AS review_id,i.id AS intern_id,i.name,i.email,i.task,r.review_date,r.review_time,r.meeting_link
             FROM reviews r JOIN interns i ON i.id=r.intern_id WHERE r.status='pending' AND r.is_followup=%s
             AND NOT EXISTS (SELECT 1 FROM email_logs e WHERE e.review_id=r.id AND e.type=%s AND e.status='sent')"""
    rows = query(sql, (fu, kind))
    if review_ids is not None: rows = [r for r in rows if r["review_id"] in review_ids]
    return rows

def preview(kind):
    rows = _targets(kind)
    if not rows: return {"count": 0, "subject": "", "body": "No pending emails."}
    s, b = render(kind, rows[0])
    return {"count": len(rows), "subject": s, "body": b, "to": rows[0]["email"]}

def prepare(kind):
    rows = _targets(kind)
    if not rows: return {"ok": False, "message": "No emails to send."}
    pid = ss.create_pending("send_emails", {"kind": kind, "review_ids": [r["review_id"] for r in rows]})
    return {"ok": True, "pending_id": pid, "count": len(rows),
            "message": f"Send {len(rows)} {kind} emails? Say yes or no."}

def prepare_single(intern_id, custom_msg=None, kind="review"):
    intern = query("SELECT * FROM interns WHERE id=%s", (intern_id,), one=True)
    if not intern:
        return {"ok": False, "message": "Intern not found."}
    rv = query("SELECT * FROM reviews WHERE intern_id=%s ORDER BY id DESC LIMIT 1", (intern_id,), one=True)
    payload = {
        "intern_id": intern["id"],
        "review_id": rv["id"] if rv else None,
        "name": intern["name"],
        "email": intern["email"],
        "kind": kind,
        "custom_msg": custom_msg,
    }
    pid = ss.create_pending("send_single_email", payload)
    target = Config.TEST_EMAIL_OVERRIDE or intern["email"]
    return {
        "ok": True,
        "pending_id": pid,
        "message": f"Send review email to {intern['name']} ({target})? Say yes to send or no to cancel."
    }

def send_single(payload):
    target = Config.TEST_EMAIL_OVERRIDE or payload["email"]
    intern_id = payload["intern_id"]
    review_id = payload.get("review_id")
    kind = payload.get("kind", "review")

    if _is_dummy_smtp():
        note = "Delivered (Demo Mode - configure real Gmail App Password in .env for live inbox delivery)"
        execute("INSERT INTO email_logs (intern_id,review_id,type,status,error) VALUES (%s,%s,%s,%s,%s)",
                (intern_id, review_id, kind, "sent", note))
        return {"sent": 1, "failed": 0, "to": target, "demo": True, "note": note}

    # Fetch review record
    rv = query("SELECT r.*, i.name, i.email, i.task FROM reviews r JOIN interns i ON i.id=r.intern_id WHERE r.id=%s",
               (review_id,), one=True) if review_id else None
    if not rv:
        rv = {"name": payload["name"], "email": payload["email"], "task": "Review",
              "review_date": "Scheduled", "review_time": "", "meeting_link": ""}

    if payload.get("custom_msg"):
        subj = f"[Notification] Review Message for {rv['name']}"
        body = payload["custom_msg"]
    else:
        subj, body = render(kind, rv)

    server = None
    try:
        server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=20)
        server.starttls()
        server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
        m = MIMEText(body)
        m["Subject"] = subj
        m["From"] = Config.SMTP_USER
        m["To"] = target
        server.sendmail(Config.SMTP_USER, [target], m.as_string())
        execute("INSERT INTO email_logs (intern_id,review_id,type,status,error) VALUES (%s,%s,%s,%s,%s)",
                (intern_id, review_id, kind, "sent", None))
        return {"sent": 1, "failed": 0, "to": target, "demo": False}
    except Exception as e:
        err = _clean_err(str(e))
        execute("INSERT INTO email_logs (intern_id,review_id,type,status,error) VALUES (%s,%s,%s,%s,%s)",
                (intern_id, review_id, kind, "failed", err))
        return {"sent": 0, "failed": 1, "error": err, "to": target}
    finally:
        if server:
            try: server.quit()
            except Exception: pass

def send_bulk(kind, review_ids):
    sent = failed = 0
    rows = _targets(kind, review_ids)

    if _is_dummy_smtp():
        note = "Delivered (Demo Mode - configure real Gmail App Password in .env for live inbox delivery)"
        for r in rows:
            execute("INSERT INTO email_logs (intern_id,review_id,type,status,error) VALUES (%s,%s,%s,%s,%s)",
                    (r["intern_id"], r["review_id"], kind, "sent", note))
            sent += 1
        return {"sent": sent, "failed": 0, "demo": True, "note": note}

    server, login_err = None, None
    try:
        server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=20)
        server.starttls()
        server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
    except Exception as e:
        login_err = _clean_err(str(e))

    for r in rows:
        err = login_err
        if not err:
            try:
                s, b = render(kind, r)
                m = MIMEText(b); m["Subject"] = s; m["From"] = Config.SMTP_USER
                to = Config.TEST_EMAIL_OVERRIDE or r["email"]; m["To"] = to
                server.sendmail(Config.SMTP_USER, [to], m.as_string())
            except Exception as e: err = _clean_err(str(e))
        execute("INSERT INTO email_logs (intern_id,review_id,type,status,error) VALUES (%s,%s,%s,%s,%s)",
                (r["intern_id"], r["review_id"], kind, "failed" if err else "sent", err))
        if err: failed += 1
        else: sent += 1
    if server:
        try: server.quit()
        except Exception: pass
    return {"sent": sent, "failed": failed, "demo": False}

def render_broadcast(subject, body, name):
    s_subj = (subject or "Announcement from HR").replace("{name}", name)
    s_body = (body or "").replace("{name}", name)
    plain = f"Hi {name},\n\n{s_body}\n\nSent by HR Team. Please do not reply."
    escaped_name = html.escape(name)
    escaped_body = html.escape(s_body).replace("\n", "<br/>")
    html_content = (
        '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
        '<body style="margin:0;padding:20px;font-family:Arial,sans-serif;background-color:#f4f6f8;color:#333;">'
        '<div style="max-width:600px;margin:0 auto;background:#ffffff;border-radius:8px;overflow:hidden;border:1px solid #e1e4e8;">'
        '<div style="background-color:#2563eb;color:#ffffff;padding:16px 20px;font-size:18px;font-weight:bold;">'
        'Intern Review Notification'
        '</div>'
        '<div style="padding:24px 20px;line-height:1.6;font-size:15px;">'
        f'<p style="margin-top:0;">Hi {escaped_name},</p>'
        f'<div style="margin:16px 0;">{escaped_body}</div>'
        '</div>'
        '<div style="background-color:#f8fafc;padding:12px 20px;border-top:1px solid #e1e4e8;font-size:12px;color:#64748b;text-align:center;">'
        'Sent by HR Team. Please do not reply.'
        '</div>'
        '</div></body></html>'
    )
    return f"[Notification] {s_subj}", plain, html_content

def prepare_broadcast(subject, body):
    subject = (subject or "").strip() or "Announcement from HR"
    body = (body or "").strip()[:2000]
    if not body:
        return {"ok": False, "pending_id": None, "count": 0, "message": "Please type a message to broadcast."}
    rows = query("SELECT id, name, email FROM interns ORDER BY id")
    seen = set()
    deduped = []
    for r in rows:
        em = (r.get("email") or "").strip().lower()
        if em and em not in seen:
            seen.add(em)
            deduped.append(r)
    if not deduped:
        return {"ok": False, "pending_id": None, "count": 0, "message": "No interns found to broadcast to."}
    intern_ids = [r["id"] for r in deduped]
    payload = {"subject": subject, "body": body, "intern_ids": intern_ids}
    pid = ss.create_pending("broadcast", payload)
    count = len(deduped)
    msg = f"Send this to {count} interns? Subject: [Notification] {subject} Message: {body} Say yes or no."
    return {"ok": True, "pending_id": pid, "count": count, "message": msg}

def send_broadcast(subject, body, intern_ids):
    sent = failed = 0
    if not intern_ids:
        return {"sent": 0, "failed": 0}

    format_strings = ','.join(['%s'] * len(intern_ids))
    rows = query(f"SELECT id, name, email FROM interns WHERE id IN ({format_strings})", tuple(intern_ids))

    if _is_dummy_smtp():
        note = "Delivered (Demo Mode - configure real Gmail App Password in .env for live inbox delivery)"
        for r in rows:
            execute("INSERT INTO email_logs (intern_id,review_id,type,status,error) VALUES (%s,%s,%s,%s,%s)",
                    (r["id"], None, "broadcast", "sent", note))
            sent += 1
        return {"sent": sent, "failed": 0, "demo": True, "note": note}

    server, login_err = None, None
    try:
        server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=20)
        server.starttls()
        server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
    except Exception as e:
        login_err = _clean_err(str(e))

    for r in rows:
        err = login_err
        if not err:
            try:
                subj, plain_text, html_text = render_broadcast(subject, body, r["name"])
                m = MIMEMultipart("alternative")
                m["Subject"] = subj
                m["From"] = Config.SMTP_USER
                to = Config.TEST_EMAIL_OVERRIDE or r["email"]
                m["To"] = to
                m.attach(MIMEText(plain_text, "plain", "utf-8"))
                m.attach(MIMEText(html_text, "html", "utf-8"))
                server.sendmail(Config.SMTP_USER, [to], m.as_string())
            except Exception as e:
                err = _clean_err(str(e))
        execute("INSERT INTO email_logs (intern_id,review_id,type,status,error) VALUES (%s,%s,%s,%s,%s)",
                (r["id"], None, "broadcast", "failed" if err else "sent", err))
        if err: failed += 1
        else: sent += 1
    if server:
        try: server.quit()
        except Exception: pass
    return {"sent": sent, "failed": failed, "demo": False}

def logs():
    return query("""SELECT e.id,i.name,i.email,e.type,e.status,e.error,e.sent_at FROM email_logs e
                    LEFT JOIN interns i ON i.id=e.intern_id ORDER BY e.id DESC LIMIT 300""")
