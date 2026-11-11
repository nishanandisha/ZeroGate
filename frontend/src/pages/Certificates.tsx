import { CertInfo } from "../api/client";
import { ErrorBanner, Pill } from "../components/ui";
import { usePoll } from "../hooks/usePoll";

export default function Certificates() {
  const { data, error } = usePoll<CertInfo[]>("/pki/certificates");
  return (
    <>
      <h1>Certificates</h1>
      <p className="sub">Every certificate in the lab PKI. Clients trust only the Root CA; the Inspection CA signs re-encrypted HTTPS.</p>
      <ErrorBanner error={error} />
      <div className="card table-wrap">
        <table>
          <thead><tr><th>Subject</th><th>Issuer</th><th>Type</th><th>Names (SAN)</th><th>Expires</th><th>Days left</th><th>State</th></tr></thead>
          <tbody>{(data ?? []).map((c) => (
            <tr key={c.file}>
              <td>{c.subject}<div className="muted mono">{c.file}</div></td>
              <td>{c.issuer}</td><td>{c.is_ca ? "CA" : "Leaf"}</td>
              <td className="mono">{c.san.join(", ") || "–"}</td>
              <td>{c.not_after.slice(0, 10)}</td><td className="num">{c.days_left}</td>
              <td><Pill kind={c.status}>{c.status === "up" ? "✓ Valid" : c.status === "degraded" ? "! Expiring soon" : "✕ Expired"}</Pill></td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </>
  );
}
