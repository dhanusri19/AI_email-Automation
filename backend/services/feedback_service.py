from db import query, execute
import services.schedule_service as ss

def add(review_id, mentor, rating, comments, outcome):
    if outcome not in ("pass", "needs_followup"): return {"ok": False, "message": "Outcome must be pass or needs_followup"}
    try:
        rating = int(rating); assert 1 <= rating <= 5
    except Exception: return {"ok": False, "message": "Rating must be 1-5"}
    if not query("SELECT id FROM reviews WHERE id=%s", (review_id,), one=True): return {"ok": False, "message": "Review not found"}
    execute("INSERT INTO feedback (review_id,mentor_name,rating,comments,outcome) VALUES (%s,%s,%s,%s,%s)",
            (review_id, mentor, rating, comments, outcome))
    ss.set_status(review_id, "completed")
    return {"ok": True, "message": "Feedback saved and review marked completed."}

def list_all():
    return query("""SELECT f.id,i.name,r.review_date,f.mentor_name,f.rating,f.comments,f.outcome FROM feedback f
                    JOIN reviews r ON r.id=f.review_id JOIN interns i ON i.id=r.intern_id ORDER BY f.id DESC""")

def suggest_followups():
    return query("""SELECT DISTINCT i.id AS intern_id,i.name,i.mentor,f.comments FROM feedback f
        JOIN reviews r ON r.id=f.review_id JOIN interns i ON i.id=r.intern_id
        WHERE f.outcome='needs_followup' AND NOT EXISTS
        (SELECT 1 FROM reviews r2 WHERE r2.intern_id=i.id AND r2.is_followup=1 AND r2.id>r.id)""")
