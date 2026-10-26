import React, { useState, useEffect } from "react";
import { api, BASE } from "../services/api";
import Table from "./Table";
export default function Dashboard() {
  const [d, setD] = useState({});
  const [rows, setRows] = useState([]);
  const [note, setNote] = useState("");
  const load = () => { api.get("/api/dashboard").then(setD).catch(() => {}); api.get("/api/reviews").then(setRows).catch(() => {}); };
  useEffect(() => { load(); }, []);
  const mark = async (id, status) => { await api.post(`/api/reviews/${id}/status`, { status }); load(); };
  const overdue = async () => { const r = await api.post("/api/reviews/flag-overdue"); setNote(`${r.flagged} overdue reviews flagged as missed`); load(); };
  const stats = [["Interns", "interns"], ["Today", "today"], ["Pending", "pending"], ["Completed", "completed"], ["Missed", "missed"], ["Emails sent", "emails_sent"], ["Emails failed", "emails_failed"]];
  return (
    <div>
      <div className="card"><div className="stats">{stats.map(([l, k]) => <div className="stat" key={k}><b>{d[k] ?? 0}</b>{l}</div>)}</div>
        <button className="btn" onClick={load}>Refresh</button>
        <button className="btn red" onClick={overdue}>Flag overdue as missed</button> {note}
        <p>Reports: {["progress", "reviews", "emails"].map((k) => (
          <span key={k}>{k}: <a href={`${BASE}/api/reports/${k}/xlsx`}>Excel</a> | <a href={`${BASE}/api/reports/${k}/pdf`}>PDF</a>&nbsp;&nbsp;</span>))}</p>
      </div>
      <div className="card"><h3>Reviews & Attendance</h3>
        <div className="scroll"><table><thead><tr><th>Intern</th><th>Date</th><th>Time</th><th>Mentor</th><th>Status</th><th>Follow-up</th><th>Mark</th></tr></thead>
          <tbody>{rows.map((r) => <tr key={r.id}><td>{r.name}</td><td>{r.review_date}</td><td>{r.review_time}</td><td>{r.mentor}</td>
            <td>{r.status}</td><td>{r.is_followup ? "yes" : ""}</td>
            <td><button className="btn green" onClick={() => mark(r.id, "completed")}>Done</button>
              <button className="btn red" onClick={() => mark(r.id, "missed")}>Missed</button></td></tr>)}</tbody></table></div>
      </div>
    </div>
  );
}
