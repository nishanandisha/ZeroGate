import { useMemo, useState } from "react";
import { TrafficEvent } from "../api/client";
import { ErrorBanner, Pill, fmtBytes, fmtTime } from "../components/ui";
import { usePoll } from "../hooks/usePoll";

export default function Traffic() {
  const { data, error } = usePoll<TrafficEvent[]>("/traffic/events?limit=300", 5000);
  const [action, setAction] = useState("");
  const [user, setUser] = useState("");
  const [q, setQ] = useState("");
  const events = data ?? [];
  const users = useMemo(() => [...new Set(events.map((e) => e.user).filter(Boolean))].sort() as string[], [events]);
  const actions = useMemo(() => [...new Set(events.map((e) => e.action))].sort(), [events]);
  const rows = events.filter((e) => (!action || e.action === action) && (!user || e.user === user) && (!q || e.url.includes(q)));

  return (
    <>
      <h1>Traffic</h1>
      <p className="sub">Unified log from the Secure Web Gateway (Squid) and the DLP proxy (mitmproxy). Refreshes every 5 seconds.</p>
      <ErrorBanner error={error} />
      <div className="filters">
        <select value={action} onChange={(e) => setAction(e.target.value)} aria-label="Filter by outcome">
          <option value="">All outcomes</option>{actions.map((a) => <option key={a}>{a}</option>)}
        </select>
        <select value={user} onChange={(e) => setUser(e.target.value)} aria-label="Filter by user">
          <option value="">All users</option>{users.map((u) => <option key={u}>{u}</option>)}
        </select>
        <input placeholder="URL contains…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Filter by URL" />
        <span className="muted">{rows.length} of {events.length} events</span>
      </div>
      <div className="card table-wrap">
        <table>
          <thead><tr><th>Time</th><th>Engine</th><th>User</th><th>Method</th><th>URL</th><th>Status</th><th>Outcome</th><th>TLS handling</th><th>Size</th></tr></thead>
          <tbody>
            {rows.map((e, i) => (
              <tr key={`${e.ts}-${i}`}>
                <td className="mono">{fmtTime(e.ts)}</td>
                <td>{e.source === "swg" ? "SWG" : "DLP"}</td>
                <td>{e.user ?? <span className="muted">{e.client ?? "–"}</span>}</td>
                <td className="mono">{e.method}</td>
                <td className="url mono" title={e.url}>{e.url}</td>
                <td className="num">{e.status ?? "–"}</td>
                <td><Pill kind={e.action} />{e.rules.length > 0 && <div className="muted">{e.rules.join(", ")}</div>}</td>
                <td>{e.inspection ?? "–"}</td>
                <td className="num">{fmtBytes(e.bytes)}</td>
              </tr>
            ))}
            {!rows.length && <tr><td colSpan={9} className="empty">No events match.</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  );
}
