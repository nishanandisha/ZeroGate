import { ReactNode } from "react";

const LABEL: Record<string, string> = {
  up: "✓ Up", degraded: "! Degraded", down: "✕ Down",
  allow: "✓ Allowed", block: "✕ Blocked", "dlp-block": "✕ DLP block", "auth-required": "! Auth required", error: "! Error",
};

/** Status is never colour alone: a symbol and a word always travel with the dot. */
export function Pill({ kind, children }: { kind: string; children?: ReactNode }) {
  const known = kind in LABEL;
  return <span className={`pill ${known ? kind : "neutral"}`}><span className="dot" />{children ?? LABEL[kind] ?? kind}</span>;
}

export function Tile({ label, value, note }: { label: string; value: ReactNode; note?: string }) {
  return (
    <div className="card tile">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {note && <div className="note">{note}</div>}
    </div>
  );
}

export function BarList({ rows, unit }: { rows: [string, number][]; unit: string }) {
  if (!rows.length) return <div className="empty">No data yet. Send some traffic through the proxy.</div>;
  const max = Math.max(...rows.map(([, v]) => v));
  return (
    <div className="bars">
      {rows.map(([k, v]) => (
        <div className="bar-row" key={k}>
          <span className="k">{k}</span>
          <span className="track"><span className="fill" style={{ width: `${(v / max) * 100}%`, display: "block" }} /></span>
          <span className="v">{v}</span>
          <span className="tip">{k}: {v} {unit}</span>
        </div>
      ))}
    </div>
  );
}

export function ErrorBanner({ error }: { error: string | null }) {
  return error ? <div className="banner" role="alert"><b>Could not refresh:</b> {error}. Showing the last data received.</div> : null;
}

export const fmtBytes = (n: number) => (n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(1)} KB` : `${(n / 1048576).toFixed(1)} MB`);
export const fmtTime = (ts: number) => new Date(ts * 1000).toLocaleTimeString();
