import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import Table from "./Table";
export default function FeedbackForm() {
  const [reviews, setReviews] = useState([]);
  const [list, setList] = useState([]);
  const [sug, setSug] = useState([]);
  const [f, setF] = useState({ review_id: "", mentor_name: "", rating: 3, comments: "", outcome: "pass" });
  const [msg, setMsg] = useState("");
  const [fu, setFu] = useState({});
  const load = () => {
    api.get("/api/reviews").then((r) => setReviews(r.filter((x) => x.status !== "rescheduled"))).catch(() => {});
    api.get("/api/feedback").then(setList).catch(() => {});
    api.get("/api/followups/suggest").then(setSug).catch(() => {});
  };
  useEffect(() => { load(); }, []);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const submit = async () => { const r = await api.post("/api/feedback", f); setMsg(r.message || r.error); load(); };
  const schedule = async (s) => {
    const v = fu[s.intern_id] || {};
    const r = await api.post("/api/schedule/request", { intern_id: s.intern_id, date: v.date, time: v.time, followup: true });
    setMsg(r.message + (r.ok ? " (Confirm on the Emails page or say 'yes' in chat.)" : ""));
  };
  return (
    <div>
      <div className="card"><h3>Mentor Feedback</h3>
        <select value={f.review_id} onChange={set("review_id")}><option value="">Select review</option>
          {reviews.map((r) => <option key={r.id} value={r.id}>{r.name} - {r.review_date} ({r.status})</option>)}</select>
        <input placeholder="Mentor name" value={f.mentor_name} onChange={set("mentor_name")} />
        <select value={f.rating} onChange={set("rating")}>{[1, 2, 3, 4, 5].map((n) => <option key={n}>{n}</option>)}</select>
        <select value={f.outcome} onChange={set("outcome")}><option value="pass">pass</option><option value="needs_followup">needs_followup</option></select><br />
        <textarea rows="3" cols="60" placeholder="Comments" value={f.comments} onChange={set("comments")} /><br />
        <button className="btn" onClick={submit}>Save Feedback</button> <b>{msg}</b>
      </div>
      <div className="card"><h3>Suggested Follow-ups</h3>
        {sug.length === 0 ? <p>None.</p> : sug.map((s) => (
          <div key={s.intern_id}>{s.name} ({s.mentor})
            <input type="date" onChange={(e) => setFu({ ...fu, [s.intern_id]: { ...fu[s.intern_id], date: e.target.value } })} />
            <input type="time" onChange={(e) => setFu({ ...fu, [s.intern_id]: { ...fu[s.intern_id], time: e.target.value } })} />
            <button className="btn" onClick={() => schedule(s)}>Request follow-up</button></div>))}
      </div>
      <div className="card"><h3>All Feedback</h3><Table rows={list} /></div>
    </div>
  );
}
