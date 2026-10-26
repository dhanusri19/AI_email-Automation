import React from "react";
export default function Table({ rows, cols }) {
  if (!rows || !rows.length) return <p>No data.</p>;
  const keys = cols || Object.keys(rows[0]);
  return (
    <div className="scroll"><table>
      <thead><tr>{keys.map((k) => <th key={k}>{k}</th>)}</tr></thead>
      <tbody>{rows.map((r, i) => <tr key={i}>{keys.map((k) => <td key={k}>{String(r[k] ?? "")}</td>)}</tr>)}</tbody>
    </table></div>
  );
}
