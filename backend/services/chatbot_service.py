import re
from db import query
import services.schedule_service as ss
import services.email_service as es
import services.feedback_service as fs
import services.report_service as rs

HELP = ("I can help with:\n- announce: <Subject> | <Message> (broadcast to all interns)\n"
        "- show <intern name>\n- show reviews today\n- show pending reviews\n- dashboard / summary\n"
        "- schedule <name> on 2026-11-02 at 10:30\n- mark <name> completed / missed\n"
        "- send review emails / send followup emails\n- suggest followups\nAnything that changes data needs you to say yes.")
SCHED = re.compile(r"(?:schedule|reschedule)\s+(.+?)\s+(?:on\s+)?(\d{4}-\d{2}-\d{2})\s+(?:at\s+)?(\d{1,2}:\d{2})")

def R(text, pending=False): return {"reply": text, "pending": pending}

def _fmt(rows, n=8):
    lines = [f"- {r['name']} | {r['review_date']} {r['review_time'][:5]} | {r['status']}" for r in rows[:n]]
    if len(rows) > n: lines.append(f"...and {len(rows)-n} more")
    return "\n".join(lines)

def process(msg):
    orig = (msg or "").strip()
    if not orig: return R("Please type or say something. Say 'help' for options.")
    
    # Broadcast intent (triggers: announce:, broadcast:, mail all:)
    orig_lower = orig.lower()
    for prefix in ("announce:", "broadcast:", "mail all:"):
        if orig_lower.startswith(prefix):
            content = orig[len(prefix):].strip()
            if not content:
                return R("Please type a message to broadcast. Format: announce: Subject | Message")
            if "|" in content:
                parts = content.split("|", 1)
                subj = parts[0].strip() or "Announcement from HR"
                body = parts[1].strip()
            else:
                subj = "Announcement from HR"
                body = content.strip()
            if not body:
                return R("Please type a message to broadcast.")
            res = es.prepare_broadcast(subj, body)
            return R(res["message"], res.get("ok", False))

    t = orig_lower
    if re.fullmatch(r"(yes|y|yeah|confirm|ok|okay|yes please)", t):
        a = ss.latest_awaiting()
        return R(ss.execute_action(a["id"]) if a else "Nothing is waiting for confirmation.")
    if re.fullmatch(r"(no|n|cancel|nope)", t):
        a = ss.latest_awaiting()
        return R(ss.cancel_action(a["id"]) if a else "Nothing to cancel.")
    if "help" in t: return R(HELP)
    m = SCHED.search(t)
    if m:
        found = ss.find_intern(m.group(1))
        if not found: return R(f"I couldn't find an intern named '{m.group(1)}'.")
        if len(found) > 1: return R("Multiple matches: " + ", ".join(f['name'] for f in found) + ". Please be specific.")
        h, mi = m.group(3).split(":")
        res = ss.request(found[0]["id"], m.group(2), f"{int(h):02d}:{mi}")
        return R(res["message"], res["ok"])
    m = re.search(r"mark\s+(.+?)\s+(completed|missed|complete)", t)
    if m:
        found = ss.find_intern(m.group(1))
        if len(found) != 1: return R("Please give one exact intern name.")
        rv = query("SELECT id FROM reviews WHERE intern_id=%s AND status='pending' ORDER BY id DESC LIMIT 1", (found[0]["id"],), one=True)
        if not rv: return R(f"{found[0]['name']} has no pending review.")
        st = "completed" if m.group(2).startswith("complete") else "missed"
        ss.set_status(rv["id"], st)
        return R(f"Marked {found[0]['name']}'s review as {st}.")

    m = re.search(r"(?:send\s+)?email\s+(?:to\s+)?([^:]+?)(?:\s*:\s*(.+))?$", t)
    if m:
        target_name = m.group(1).strip()
        custom_msg = m.group(2).strip() if m.group(2) else None
        if target_name not in ("review emails", "followup emails", "review email", "followup email", "all", "emails"):
            found = ss.find_intern(target_name)
            if not found and any(w in target_name for w in ("anyone", "any intern", "any", "someone")):
                rows = query("SELECT * FROM interns ORDER BY id LIMIT 1")
                if rows: found = rows
            if found:
                if len(found) > 1 and not any(w in target_name for w in ("anyone", "any intern", "any", "someone")):
                    return R("Multiple matches: " + ", ".join(f['name'] for f in found[:5]) + ". Please specify exact name.")
                intern = found[0]
                res = es.prepare_single(intern["id"], custom_msg=custom_msg)
                return R(res["message"], res["ok"])

    if "send" in t and "email" in t:
        kind = "followup" if "follow" in t else "review"
        res = es.prepare(kind)
        return R(res["message"], res["ok"])
    if "suggest" in t or "follow" in t:
        s = fs.suggest_followups()
        if not s: return R("No follow-ups needed right now.")
        return R("Interns needing follow-up:\n" + "\n".join(f"- {x['name']}" for x in s) + "\nSay 'schedule <name> on YYYY-MM-DD at HH:MM' to book one.")
    if "today" in t and "review" in t:
        rows = ss.list_reviews(today=True)
        return R(f"{len(rows)} reviews today.\n" + _fmt(rows) if rows else "No reviews scheduled today.")
    if "pending" in t:
        rows = [r for r in ss.list_reviews() if r["status"] == "pending"]
        return R(f"{len(rows)} pending reviews.\n" + _fmt(rows) if rows else "No pending reviews.")
    if any(w in t for w in ("dashboard", "summary", "stats")):
        d = rs.dashboard()
        return R(f"{d['interns']} interns. Reviews: {d['completed']} completed, {d['pending']} pending, {d['missed']} missed. "
                 f"Emails: {d['emails_sent']} sent, {d['emails_failed']} failed.")
    m = re.search(r"(?:show|find|details?(?: of)?|who is)\s+(?:intern\s+)?(.+)", t)
    if m:
        rows = query("""SELECT i.name,i.email,i.task,i.mentor,r.review_date,r.review_time,r.status FROM interns i
            LEFT JOIN reviews r ON r.id=(SELECT MAX(id) FROM reviews WHERE intern_id=i.id) WHERE i.name LIKE %s LIMIT 5""",
            (f"%{m.group(1).strip()}%",))
        if not rows: return R(f"No intern found matching '{m.group(1)}'.")
        return R("\n".join(f"{r['name']} ({r['email']}) - Task: {r['task']} - Mentor: {r['mentor']} - Review: "
                           f"{r['review_date']} {str(r['review_time'])[:5]} ({r['status']})" for r in rows))
    return R("Sorry, I didn't understand that. Say 'help' to see what I can do.")
