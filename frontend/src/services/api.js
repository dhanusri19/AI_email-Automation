export const BASE = "http://localhost:5000";
const j = (r) => r.json();
export const api = {
  get: (u) => fetch(BASE + u).then(j),
  post: (u, b) => fetch(BASE + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) }).then(j),
  upload: (file, sheet_name) => { const d = new FormData(); d.append("file", file); if (sheet_name) d.append("sheet_name", sheet_name); return fetch(BASE + "/api/upload", { method: "POST", body: d }).then(j); },
};
