import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import Table from "./Table";

export default function UploadPanel() {
  const [file, setFile] = useState(null);
  const [selectedSheet, setSelectedSheet] = useState("");
  const [result, setResult] = useState(null);
  const [interns, setInterns] = useState([]);
  const [busy, setBusy] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  const load = () => api.get("/api/interns").then(setInterns).catch(() => {});
  useEffect(() => { load(); }, []);

  const handleUpload = async (sheetOverride) => {
    if (!file) return alert("Choose an .xlsx or .xls file first");
    setBusy(true);
    const sheetToUse = sheetOverride !== undefined ? sheetOverride : selectedSheet;
    try {
      const res = await api.upload(file, sheetToUse);
      setResult(res);
      if (res.sheet_analyzed) setSelectedSheet(res.sheet_analyzed);
      load();
    } catch (e) {
      setResult({ error: String(e) });
    }
    setBusy(false);
  };

  const handleSheetChange = (newSheet) => {
    setSelectedSheet(newSheet);
    handleUpload(newSheet);
  };

  const filteredInterns = interns.filter((i) => {
    const term = searchTerm.toLowerCase();
    return (
      (i.name && i.name.toLowerCase().includes(term)) ||
      (i.email && i.email.toLowerCase().includes(term)) ||
      (i.task && i.task.toLowerCase().includes(term)) ||
      (i.mentor && i.mentor.toLowerCase().includes(term))
    );
  });

  return (
    <div>
      <div className="card">
        <h3>Upload & Analyze Candidate / Intern Excel</h3>
        <p style={{ color: "#555", fontSize: "0.9em", margin: "4px 0 12px 0" }}>
          Upload your review schedule file. Automatically detects columns like <b>Candidate Name / Name</b>, <b>Email ID / Email</b>, <b>Task</b>, <b>Review Date</b>, <b>Review Time</b>, and <b>Meeting Link</b> across any workbook tab.
        </p>

        <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap", marginBottom: 12 }}>
          <input
            type="file"
            accept=".xlsx,.xls"
            onChange={(e) => {
              setFile(e.target.files[0]);
              setResult(null);
              setSelectedSheet("");
            }}
          />
          <button className="btn" onClick={() => handleUpload()} disabled={busy || !file}>
            {busy ? "Analyzing & Saving..." : "Upload & Analyze"}
          </button>
        </div>

        {/* Tab/Sheet Switcher if workbook has multiple sheets */}
        {result && result.available_sheets && result.available_sheets.length > 1 && (
          <div style={{ marginTop: 12, padding: "10px", background: "#f0f4f8", borderRadius: 8 }}>
            <span style={{ fontSize: "0.9em", fontWeight: "bold", marginRight: 10 }}>Workbook Sheet / Tab:</span>
            {result.available_sheets.map((s) => (
              <button
                key={s}
                className={"btn " + (result.sheet_analyzed === s ? "green" : "")}
                style={{ fontSize: "0.85em", padding: "4px 10px" }}
                onClick={() => handleSheetChange(s)}
                disabled={busy}
              >
                {s} {result.sheet_analyzed === s ? "✓ (Active)" : ""}
              </button>
            ))}
          </div>
        )}

        {/* Error message */}
        {result && result.error && (
          <div style={{ marginTop: 12, padding: 10, background: "#fde8e8", borderRadius: 6 }}>
            <p className="err" style={{ margin: 0, fontWeight: "bold" }}>❌ {result.error}</p>
          </div>
        )}

        {/* Rich Analysis Dashboard */}
        {result && result.analysis && !result.error && (
          <div style={{ marginTop: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "2px solid #eef2f8", paddingBottom: 6 }}>
              <h4 style={{ margin: 0, color: "#1f3a5f" }}>
                📊 Analysis of Sheet: <i>"{result.sheet_analyzed}"</i>
              </h4>
              <span className="ok" style={{ fontWeight: "bold", fontSize: "0.9em" }}>
                ✓ Successfully Analyzed & Saved
              </span>
            </div>

            {/* Metric counters */}
            <div className="stats" style={{ margin: "12px 0" }}>
              <div className="stat">
                <b>{result.total}</b>
                <span>Total Rows</span>
              </div>
              <div className="stat">
                <b style={{ color: "#2e8b57" }}>{result.saved}</b>
                <span>Saved to Database</span>
              </div>
              <div className="stat">
                <b style={{ color: result.error_count > 0 ? "#c0392b" : "#666" }}>{result.error_count}</b>
                <span>Errors / Skipped</span>
              </div>
              {result.analysis.date_range && result.analysis.date_range.start && (
                <div className="stat" style={{ minWidth: 180 }}>
                  <span style={{ fontSize: "1.1em", fontWeight: "bold", display: "block", marginTop: 4 }}>
                    {result.analysis.date_range.start} → {result.analysis.date_range.end}
                  </span>
                  <span>Scheduled Range</span>
                </div>
              )}
            </div>

            {/* Task & Status Breakdown */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12, margin: "12px 0" }}>
              {/* Top Tasks */}
              {result.analysis.tasks_summary && Object.keys(result.analysis.tasks_summary).length > 0 && (
                <div style={{ background: "#f9fafb", padding: 10, borderRadius: 8, border: "1px solid #e5e7eb" }}>
                  <div style={{ fontWeight: "bold", marginBottom: 6, fontSize: "0.85em", color: "#374151" }}>Tasks / Domains Found:</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {Object.entries(result.analysis.tasks_summary).map(([task, count]) => (
                      <span key={task} style={{ background: "#e5edff", color: "#1e40af", padding: "3px 8px", borderRadius: 4, fontSize: "0.8em" }}>
                        {task} <b>({count})</b>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Status Breakdown */}
              {result.analysis.status_summary && Object.keys(result.analysis.status_summary).length > 0 && (
                <div style={{ background: "#f9fafb", padding: 10, borderRadius: 8, border: "1px solid #e5e7eb" }}>
                  <div style={{ fontWeight: "bold", marginBottom: 6, fontSize: "0.85em", color: "#374151" }}>Schedule Status Breakdown:</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {Object.entries(result.analysis.status_summary).map(([status, count]) => (
                      <span key={status} style={{ background: "#e6fffa", color: "#047857", padding: "3px 8px", borderRadius: 4, fontSize: "0.8em" }}>
                        {status}: <b>{count}</b>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Detected Columns */}
            {result.analysis.columns_detected && (
              <div style={{ fontSize: "0.8em", color: "#555", marginTop: 6, background: "#f8fafc", padding: "6px 10px", borderRadius: 6 }}>
                <b>Recognized Columns from Excel: </b>
                {Object.entries(result.analysis.columns_detected).map(([std, orig]) => (
                  <span key={std} style={{ marginRight: 8, display: "inline-block" }}>
                    <code>{orig}</code> ➔ <i>{std}</i>
                  </span>
                ))}
              </div>
            )}

            {/* Errors List if any */}
            {result.error_count > 0 && (
              <div style={{ marginTop: 12 }}>
                <p className="err" style={{ fontWeight: "bold", margin: "6px 0" }}>
                  ⚠️ {result.error_count} row(s) had errors and were not saved:
                </p>
                <Table rows={result.errors} cols={["row", "name", "error"]} />
              </div>
            )}

            {/* Preview of Uploaded Data */}
            {result.analysis.preview && result.analysis.preview.length > 0 && (
              <div style={{ marginTop: 14 }}>
                <div style={{ fontWeight: "bold", fontSize: "0.9em", color: "#1f3a5f", marginBottom: 4 }}>
                  📋 Uploaded Data Preview (Showing first {result.analysis.preview.length} rows):
                </div>
                <Table
                  rows={result.analysis.preview}
                  cols={["Name", "Email", "Task", "Review Date", "Review Time", "Status", "Meeting Link"]}
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Database Interns List */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", marginBottom: 10 }}>
          <h3 style={{ margin: 0 }}>All Interns in Database ({interns.length})</h3>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input
              type="text"
              placeholder="Search by name, email, task..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ width: 220 }}
            />
            <button className="btn" onClick={load}>Refresh</button>
          </div>
        </div>
        {interns.length === 0 ? (
          <p style={{ color: "#777" }}>No interns in database yet. Upload an Excel file above to import them.</p>
        ) : (
          <Table
            rows={filteredInterns}
            cols={["id", "name", "email", "task", "mentor", "review_date", "review_time", "review_status"]}
          />
        )}
      </div>
    </div>
  );
}
