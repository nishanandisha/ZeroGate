"""ZeroGate DLP addon for mitmproxy.

Blocks uploads (POST/PUT/PATCH) whose body matches sensitive-data rules and writes one JSON line per flow
to /logs/flows.jsonl for the control plane.
"""
import json
import re
import time

from mitmproxy import http

LOG = "/logs/flows.jsonl"
RULES = {
    "credit_card": re.compile(rb"\b(?:4\d{3}|5[1-5]\d{2})[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b"),
    "us_ssn": re.compile(rb"\b\d{3}-\d{2}-\d{4}\b"),
    "aws_access_key": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "classified_marker": re.compile(rb"(?i)\bzerogate[- ]confidential\b"),
}
UPLOAD_METHODS = {"POST", "PUT", "PATCH"}


def _write(entry: dict) -> None:
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def _entry(flow: http.HTTPFlow, action: str, extra: dict | None = None) -> dict:
    req = flow.request
    e = {
        "ts": round(time.time(), 3),
        "client": flow.client_conn.peername[0] if flow.client_conn.peername else None,
        "method": req.method,
        "host": req.pretty_host,
        "url": req.pretty_url,
        "tls": req.scheme == "https",
        "status": flow.response.status_code if flow.response else None,
        "bytes": len(flow.response.raw_content or b"") if flow.response else 0,
        "req_bytes": len(req.raw_content or b""),
        "action": action,
    }
    if extra:
        e.update(extra)
    return e


class ZeroGateDLP:
    def request(self, flow: http.HTTPFlow) -> None:
        if flow.request.method not in UPLOAD_METHODS:
            return
        body = flow.request.raw_content or b""
        hits = [name for name, rx in RULES.items() if rx.search(body)]
        if hits:
            flow.metadata["zg_dlp"] = hits
            flow.response = http.Response.make(
                403,
                json.dumps({"blocked_by": "ZeroGate DLP", "rules": hits}),
                {"Content-Type": "application/json", "X-ZeroGate-Action": "dlp-block"},
            )

    def response(self, flow: http.HTTPFlow) -> None:
        hits = flow.metadata.get("zg_dlp")
        _write(_entry(flow, "dlp-block" if hits else "allow", {"dlp_rules": hits or []}))

    def error(self, flow: http.HTTPFlow) -> None:
        _write(_entry(flow, "error", {"error": str(flow.error)}))


addons = [ZeroGateDLP()]
