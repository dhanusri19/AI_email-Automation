import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import Table from "./Table";

export default function EmailStatus() {
  const [kind, setKind] = useState("review");
  const [prev, setPrev] = useState(null);
  const [logs, setLogs] = useState([]);
  const [pending, setPending] = useState([]);
  const [msg, setMsg] = useState("");
  const [bcSubject, setBcSubject] = useState("");
  const [bcBody, setBcBody] = useState("");

  const load = () => {
    api.get("/api/email/logs").then(setLogs).catch(() => {});
    api.get("/api/pending").then(setPending).catch(() => {});
  };

  useEffect(() => { load(); }, []);

  const preview = async () => setPrev(await api.get(`/api/email/preview?kind=${kind}`));
  const prepare = async () => {
    const r = await api.post("/api/email/prepare", { kind });
    setMsg(r.message);
    load();
  };
  const prepareBroadcast = async () => {
    if (!bcBody.trim()) {
      setMsg("Please enter a message to broadcast.");
      return;
    }
    const r = await api.post("/api/email/broadcast/prepare", { subject: bcSubject, body: bcBody });
    setMsg(r.message);
    if (r.ok) {
      setBcSubject("");
      setBcBody("");
    }
    load();
  };
  const act = async (id, a) => {
    const r = await api.post(`/api/pending/${id}/${a}`);
    setMsg(r.message);
    load();
  };

  return (
    <div>
      <div className="card">
        <h3>Send message to all interns</h3>
        <input
          style={{ width: "100%", marginBottom: 8, padding: 6, boxSizing: "border-box" }}
          placeholder="Subject (e.g. Announcement from HR)"
          value={bcSubject}
          onChange={(e) => setBcSubject(e.target.value)}
        />
        <textarea
          style={{ width: "100%", height: 80, padding: 6, boxSizing: "border-box" }}
          placeholder="Type your message here..."
          value={bcBody}
          onChange={(e) => setBcBody(e.target.value)}
        />
        <p style={{ margin: "4px 0 8px 0", fontSize: "0.85em", color: "#666" }}>
          Use {"{name}"} for the intern's name
        </p>
        <button className="btn green" onClick={prepareBroadcast}>Prepare broadcast</button>
      </div>

      <div className="card"><h3>Send Emails</h3>
        <select value={kind} onChange={(e) => setKind(e.target.value)}>
          <option value="review">Review emails</option>
          <option value="followup">Follow-up emails</option>
        </select>
        <button className="btn" onClick={preview}>Preview</button>
        <button className="btn green" onClick={prepare}>Prepare bulk send</button>
        {msg && <p><b>{msg}</b></p>}
        {prev && <div><p>Recipients: {prev.count} {prev.to && `(sample: ${prev.to})`}</p><pre>{prev.subject}{"\n\n"}{prev.body}</pre></div>}
      </div>

      <div className="card"><h3>Waiting for HR confirmation</h3>
        {pending.length === 0 ? <p>Nothing pending.</p> : pending.map((p) => (
          <div key={p.id} style={{ marginBottom: 8 }}>
            #{p.id} <b>{p.action_type}</b> {JSON.stringify(p.payload).slice(0, 90)}
            <button className="btn green" onClick={() => act(p.id, "confirm")}>Yes, execute</button>
            <button className="btn red" onClick={() => act(p.id, "cancel")}>No, cancel</button>
          </div>))}
      </div>

      <div className="card"><h3>Email Logs</h3><button className="btn" onClick={load}>Refresh</button>
        <Table rows={logs} cols={["name", "email", "type", "status", "error", "sent_at"]} /></div>
    </div>
  );
}
