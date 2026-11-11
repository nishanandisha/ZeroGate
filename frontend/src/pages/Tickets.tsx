import DOMPurify from "dompurify";
import { marked } from "marked";
import { useEffect, useMemo, useState } from "react";
import { Scenario, Ticket, TicketSummary, api } from "../api/client";
import { ErrorBanner, Pill } from "../components/ui";
import { usePoll } from "../hooks/usePoll";

export default function Tickets() {
  const list = usePoll<TicketSummary[]>("/tickets");
  const scenarios = usePoll<Scenario[]>("/scenarios");
  const [sel, setSel] = useState<string | null>(null);
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => { if (!sel && list.data?.length) setSel(list.data[0].id); }, [list.data, sel]);
  useEffect(() => {
    if (!sel) return;
    api<Ticket>(`/tickets/${sel}`).then((t) => { setTicket(t); setErr(null); }).catch((e: Error) => setErr(e.message));
  }, [sel]);
  // Ticket markdown comes from the repo, but it is still sanitised before it touches the DOM.
  const html = useMemo(() => (ticket ? DOMPurify.sanitize(marked.parse(ticket.markdown, { async: false })) : ""), [ticket]);
  const scenario = scenarios.data?.find((s) => s.ticket === sel);

  return (
    <>
      <h1>Support tickets</h1>
      <p className="sub">Faults injected on purpose, then diagnosed and fixed. Each ticket has a script that reproduces it.</p>
      <ErrorBanner error={list.error ?? err} />
      <div className="ticket-layout">
        <div className="card ticket-list">
          {(list.data ?? []).map((t) => (
            <button key={t.id} className={t.id === sel ? "sel" : ""} onClick={() => setSel(t.id)}>
              <div className="tid">{t.id} · {t.severity} · {t.component}</div>
              <div>{t.title}</div>
            </button>
          ))}
          {list.data?.length === 0 && <div className="empty">No tickets yet.</div>}
        </div>
        <div className="card">
          {scenario && <p><Pill kind="scenario">Reproduce</Pill> <code>make break S={scenario.id}</code> → <code>make verify S={scenario.id}</code> → <code>make fix S={scenario.id}</code></p>}
          <div className="md" dangerouslySetInnerHTML={{ __html: html }} />
        </div>
      </div>
    </>
  );
}
