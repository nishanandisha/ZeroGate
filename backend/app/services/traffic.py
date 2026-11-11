"""Normalise Squid (SWG) and mitmproxy (DLP) logs into one event stream + aggregate stats."""
import json
from collections import Counter
from pathlib import Path

from app.schemas.models import TrafficEvent


def tail_lines(path: str, n: int) -> list[str]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("rb") as fh:
        fh.seek(0, 2)
        size = fh.tell()
        block, data = 8192, b""
        while size > 0 and data.count(b"\n") <= n:
            step = min(block, size)
            size -= step
            fh.seek(size)
            data = fh.read(step) + data
    return [ln for ln in data.decode(errors="replace").splitlines() if ln.strip()][-n:]


def from_squid(line: str) -> TrafficEvent | None:
    try:
        d = json.loads(line)
    except json.JSONDecodeError:
        return None
    if d.get("method") in ("-", None):  # connection closed before any request (health checks, port scans)
        return None
    status = int(d.get("status") or 0)
    user = d.get("user") if d.get("user") not in ("-", "", None) else None
    if status == 407:
        action = "auth-required"
    elif status == 403 and str(d.get("action", "")).startswith(("NONE", "TCP_DENIED")):
        action = "block"
    elif status == 0 or status >= 500:
        action = "error"
    else:
        action = "allow"
    bump = d.get("bump")
    return TrafficEvent(
        ts=float(d["ts"]), source="swg", user=user, client=d.get("client"), method=d.get("method", "?"),
        host=next((h for h in (d.get("host"), d.get("sni")) if h not in ("-", "", None)), None),
        url=d.get("url", ""), status=status or None, bytes=int(d.get("bytes") or 0),
        action=action, inspection=None if bump in ("-", None) else bump,
    )


def from_mitm(line: str) -> TrafficEvent | None:
    try:
        d = json.loads(line)
    except json.JSONDecodeError:
        return None
    return TrafficEvent(
        ts=float(d["ts"]), source="dlp", user=None, client=d.get("client"), method=d.get("method", "?"),
        host=d.get("host"), url=d.get("url", ""), status=d.get("status"), bytes=int(d.get("bytes") or 0),
        action=d.get("action", "allow"), inspection="decrypt" if d.get("tls") else "plain", rules=d.get("dlp_rules") or [],
    )


def events(squid_log: str, mitm_log: str, limit: int = 200) -> list[TrafficEvent]:
    ev = [e for e in map(from_squid, tail_lines(squid_log, limit)) if e]
    ev += [e for e in map(from_mitm, tail_lines(mitm_log, limit)) if e]
    # CONNECT rows from a bumped tunnel duplicate the inner request; keep them (they carry the bump decision)
    return sorted(ev, key=lambda e: e.ts, reverse=True)[:limit]


def stats(ev: list[TrafficEvent]) -> dict:
    actions = Counter(e.action for e in ev)
    return {
        "total": len(ev),
        "by_action": dict(actions),
        "blocked": actions.get("block", 0) + actions.get("dlp-block", 0),
        "by_inspection": dict(Counter(e.inspection for e in ev if e.inspection)),
        "top_hosts": Counter(e.host for e in ev if e.host).most_common(8),
        "top_users": Counter(e.user for e in ev if e.user).most_common(8),
        "dlp_rules": dict(Counter(r for e in ev for r in e.rules)),
        "bytes": sum(e.bytes for e in ev),
    }
