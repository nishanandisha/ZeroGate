import { ComponentHealth, TrafficStats } from "../api/client";
import { BarList, ErrorBanner, Pill, Tile, fmtBytes } from "../components/ui";
import { usePoll } from "../hooks/usePoll";

export default function Dashboard() {
  const health = usePoll<ComponentHealth[]>("/health/components", 10000);
  const stats = usePoll<TrafficStats>("/traffic/stats", 10000);
  const comps = health.data ?? [];
  const up = comps.filter((c) => c.status === "up").length;
  const s = stats.data;
  const inspected = s ? (s.by_inspection.bump ?? 0) + (s.by_inspection.decrypt ?? 0) : 0;

  return (
    <>
      <h1>Overview</h1>
      <p className="sub">Live state of the tunnel, inspection and identity planes. Refreshes every 10 seconds.</p>
      <ErrorBanner error={health.error ?? stats.error} />
      <div className="grid tiles">
        <Tile label="Components healthy" value={comps.length ? `${up} / ${comps.length}` : "–"} note={up === comps.length ? "All systems operational" : "Attention needed"} />
        <Tile label="Requests (recent window)" value={s?.total ?? "–"} note={s ? fmtBytes(s.bytes) + " transferred" : undefined} />
        <Tile label="Blocked by policy" value={s?.blocked ?? "–"} note="URL policy + DLP" />
        <Tile label="TLS inspected" value={s ? inspected : "–"} note={s ? `${s.by_inspection.splice ?? 0} bypassed (privacy list)` : undefined} />
      </div>

      <h2>Components</h2>
      <div className="grid comp-grid" style={{ marginBottom: 22 }}>
        {comps.map((c) => (
          <div className="card comp" key={c.id}>
            <header>
              <div><div className="cat">{c.category}</div><div className="name">{c.name}</div></div>
              <Pill kind={c.status} />
            </header>
            <div className="detail">{c.detail}</div>
            <div className="lat">probe {c.latency_ms ?? "–"} ms</div>
          </div>
        ))}
        {!comps.length && !health.error && <div className="empty">Probing components…</div>}
      </div>

      <div className="grid cols-2">
        <div className="card"><h2>Top destinations (requests)</h2><BarList rows={s?.top_hosts ?? []} unit="requests" /></div>
        <div className="card"><h2>Requests by user</h2><BarList rows={s?.top_users ?? []} unit="requests" /></div>
        <div className="card"><h2>Requests by outcome</h2><BarList rows={Object.entries(s?.by_action ?? {}).sort((a, b) => b[1] - a[1])} unit="requests" /></div>
        <div className="card"><h2>DLP rule hits</h2><BarList rows={Object.entries(s?.dlp_rules ?? {}).sort((a, b) => b[1] - a[1])} unit="hits" /></div>
      </div>
    </>
  );
}
