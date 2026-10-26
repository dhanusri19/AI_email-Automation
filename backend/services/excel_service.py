import io
import re
from datetime import datetime, time
import pandas as pd
from db import query, execute

REQUIRED_CORE = ["name", "email"]

SYNONYMS = {
    "name": ["name", "candidatename", "internname", "fullname", "candidate", "intern", "studentname"],
    "email": ["email", "emailid", "candidateemail", "internemail", "emailaddress", "mailid", "mail"],
    "task": ["task", "project", "role", "domain", "topic", "assignment", "tasktitle", "taskname", "taskstatus"],
    "mentor": ["mentor", "mentorname", "reviewer", "reviewername", "interviewer", "lead", "assignedmentor"],
    "review_date": ["reviewdate", "date", "interviewdate", "meetingdate", "scheduledate", "nextfollowupdate"],
    "review_time": ["reviewtime", "time", "interviewtime", "meetingtime", "scheduletime", "slot"],
    "meeting_link": ["meetinglink", "googlemeetlink", "meetlink", "googlemeet", "link", "meetingurl", "url", "zoomlink"],
    "status": ["reviewstatus", "status"],
    "candidate_id": ["candidateid", "internid", "id", "rollno", "candidatecode"],
    "feedback": ["reviewerfeedback", "feedback", "comments", "notes"],
}

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")

def clean_col(c):
    return re.sub(r"[^a-z0-9]", "", str(c).lower())

def _parse_date(val):
    if not val or pd.isna(val): return None
    s = str(val).strip()
    if not s or s.lower() in ("nan", "nat", "none", "null"): return None
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime("%Y-%m-%d")
    s10 = s[:10]
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s10, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.notnull(dt):
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    return None

def _parse_time(val):
    if not val or pd.isna(val): return None
    s = str(val).strip()
    if not s or s.lower() in ("nan", "nat", "none", "null"): return None
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime("%H:%M:%S")
    for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p"):
        try:
            return datetime.strptime(s, fmt).strftime("%H:%M:%S")
        except ValueError:
            pass
    m = re.match(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$", s)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        sec = int(m.group(3)) if m.group(3) else 0
        return f"{h:02d}:{mi:02d}:{sec:02d}"
    return None

def _parse_status(val):
    s = str(val).strip().lower()
    if s in ("completed", "done", "passed", "pass"): return "completed"
    if s in ("missed", "absent", "failed", "fail"): return "missed"
    if s in ("rescheduled", "postponed"): return "rescheduled"
    return "pending"

def _score_sheet(df):
    cols = [clean_col(c) for c in df.columns]
    score = 0
    for std_name, syns in SYNONYMS.items():
        if any(norm in syns for norm in cols):
            score += 3 if std_name in REQUIRED_CORE else 1
    return score

def validate(file, sheet_name=None):
    """
    Validates Excel file. Supports multiple sheets/tabs, auto-selects the best data sheet
    or reads the requested sheet_name. Returns (valid_rows, errors, total_rows, analysis).
    """
    try:
        if hasattr(file, "read"):
            content = file.read()
            if hasattr(file, "seek"):
                file.seek(0)
            xl = pd.ExcelFile(io.BytesIO(content))
        else:
            xl = pd.ExcelFile(file)
    except Exception as e:
        err = [{"row": 0, "error": f"Cannot read Excel file: {e}"}]
        return [], err, 0, {"error": str(e), "sheet_analyzed": "", "available_sheets": []}

    available_sheets = xl.sheet_names
    chosen_sheet = None

    if sheet_name and sheet_name in available_sheets:
        chosen_sheet = sheet_name
    else:
        # Auto-detect sheet with the best candidate/review column matches
        best_sheet = available_sheets[0]
        best_score = -1
        for s in available_sheets:
            try:
                sample_df = pd.read_excel(xl, sheet_name=s, nrows=5)
                score = _score_sheet(sample_df)
                if score > best_score:
                    best_score = score
                    best_sheet = s
            except Exception:
                pass
        chosen_sheet = best_sheet

    try:
        df = pd.read_excel(xl, sheet_name=chosen_sheet, dtype=str).fillna("")
    except Exception as e:
        err = [{"row": 0, "error": f"Cannot read sheet '{chosen_sheet}': {e}"}]
        return [], err, 0, {"error": str(e), "sheet_analyzed": chosen_sheet, "available_sheets": available_sheets}

    # Match column synonyms
    col_map = {}
    for col in df.columns:
        norm = clean_col(col)
        for std_name, syns in SYNONYMS.items():
            if norm in syns and std_name not in col_map:
                col_map[std_name] = col

    missing_core = [k for k in REQUIRED_CORE if k not in col_map]
    if missing_core:
        readable_missing = ["Name (or Candidate Name)" if c == "name" else "Email (or Email ID)" for c in missing_core]
        err = [{"row": 0, "error": f"Missing required columns in sheet '{chosen_sheet}': " + ", ".join(readable_missing)}]
        return [], err, len(df), {
            "sheet_analyzed": chosen_sheet,
            "available_sheets": available_sheets,
            "total_rows": len(df),
            "columns_detected": col_map,
            "error": "Missing essential columns",
        }

    valid, errors, seen = [], [], set()
    dates_list = []
    task_counts = {}
    status_counts = {}
    mentor_counts = {}

    for i, r in df.iterrows():
        n = i + 2
        errs = []

        name = str(r[col_map["name"]]).strip() if "name" in col_map else ""
        raw_email = str(r[col_map["email"]]).strip() if "email" in col_map else ""
        email = raw_email.lower()

        task = str(r[col_map["task"]]).strip() if "task" in col_map else "General Review"
        if not task: task = "General Review"

        mentor = str(r[col_map["mentor"]]).strip() if "mentor" in col_map else "HR Mentor"
        if not mentor: mentor = "HR Mentor"

        raw_date = str(r[col_map["review_date"]]).strip() if "review_date" in col_map else ""
        date = _parse_date(raw_date) if raw_date else "2026-11-01"

        raw_time = str(r[col_map["review_time"]]).strip() if "review_time" in col_map else ""
        time_val = _parse_time(raw_time) if raw_time else "10:00:00"

        link = str(r[col_map["meeting_link"]]).strip() if "meeting_link" in col_map else ""

        raw_status = str(r[col_map["status"]]).strip() if "status" in col_map else "pending"
        status_val = _parse_status(raw_status)

        cid = str(r[col_map["candidate_id"]]).strip() if "candidate_id" in col_map else f"C{n:03d}"

        if not name:
            errs.append("Candidate/Intern Name is missing")
        if not raw_email:
            errs.append("Email is missing")
        elif not EMAIL_RE.match(email):
            errs.append(f"Invalid email format: '{raw_email}'")
        elif email in seen:
            errs.append("Duplicate email in file")

        if not date:
            errs.append(f"Invalid Review Date: '{raw_date}' (expected YYYY-MM-DD)")
        if not time_val:
            errs.append(f"Invalid Review Time: '{raw_time}' (expected HH:MM)")

        if errs:
            errors.append({"row": n, "name": name or f"Row {n}", "error": "; ".join(errs)})
        else:
            seen.add(email)
            record = {
                "Candidate ID": cid,
                "Name": name,
                "Email": email,
                "Task": task,
                "Mentor": mentor,
                "Review Date": date,
                "Review Time": time_val,
                "Meeting Link": link,
                "Status": status_val,
            }
            valid.append(record)
            dates_list.append(date)
            task_counts[task] = task_counts.get(task, 0) + 1
            status_display = raw_status.title() if raw_status else "Scheduled"
            status_counts[status_display] = status_counts.get(status_display, 0) + 1
            mentor_counts[mentor] = mentor_counts.get(mentor, 0) + 1

    sorted_dates = sorted(dates_list)
    analysis = {
        "sheet_analyzed": chosen_sheet,
        "available_sheets": available_sheets,
        "total_rows": len(df),
        "valid_rows": len(valid),
        "error_count": len(errors),
        "tasks_summary": dict(sorted(task_counts.items(), key=lambda x: x[1], reverse=True)[:8]),
        "status_summary": status_counts,
        "mentors_summary": dict(sorted(mentor_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
        "date_range": {
            "start": sorted_dates[0] if sorted_dates else "",
            "end": sorted_dates[-1] if sorted_dates else "",
        },
        "columns_detected": {std: orig for std, orig in col_map.items()},
        "preview": valid[:10],
    }

    return valid, errors, len(df), analysis

def save(valid, filename, total, errors):
    for r in valid:
        execute("""INSERT INTO interns (name,email,task,mentor) VALUES (%s,%s,%s,%s)
                   ON DUPLICATE KEY UPDATE name=VALUES(name),task=VALUES(task),mentor=VALUES(mentor)""",
                (r["Name"], r["Email"], r["Task"], r["Mentor"]))
        iid = query("SELECT id FROM interns WHERE email=%s", (r["Email"],), one=True)["id"]
        st = r.get("Status", "pending")
        if not query("SELECT id FROM reviews WHERE intern_id=%s AND review_date=%s AND review_time=%s AND is_followup=0",
                     (iid, r["Review Date"], r["Review Time"]), one=True):
            execute("INSERT INTO reviews (intern_id,review_date,review_time,meeting_link,mentor,status) VALUES (%s,%s,%s,%s,%s,%s)",
                    (iid, r["Review Date"], r["Review Time"], r["Meeting Link"], r["Mentor"], st))
        else:
            execute("UPDATE reviews SET status=%s, meeting_link=%s, mentor=%s WHERE intern_id=%s AND review_date=%s AND review_time=%s AND is_followup=0",
                    (st, r["Meeting Link"], r["Mentor"], iid, r["Review Date"], r["Review Time"]))
    execute("INSERT INTO upload_batches (filename,total_rows,valid_rows,error_rows) VALUES (%s,%s,%s,%s)",
            (filename, total, len(valid), len(errors)))

def list_interns():
    return query("""SELECT i.id,i.name,i.email,i.task,i.mentor,i.status,r.review_date,r.review_time,
                    r.meeting_link,r.status AS review_status FROM interns i
                    LEFT JOIN reviews r ON r.id=(SELECT MAX(id) FROM reviews WHERE intern_id=i.id)
                    ORDER BY i.id""")
