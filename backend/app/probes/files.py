"""Probes that read status files published by the VPN gateways, plus the PKI inventory."""
import time
from pathlib import Path

from app.core.config import Settings
from app.services import pki


def parse_wg_dump(text: str, now: float, stale_s: int) -> dict:
    """Parse `wg show wg0 dump` (+ our '# ts=.. ip_forward=..' header)."""
    meta: dict = {}
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if lines and lines[0].startswith("#"):
        meta = dict(kv.split("=", 1) for kv in lines[0][1:].split())
        lines = lines[1:]
    peers = []
    for ln in lines[1:]:  # first line = interface
        f = ln.split("\t")
        if len(f) < 8:
            continue
        hs = int(f[4])
        peers.append({
            "public_key": f[0][:10] + "…", "endpoint": None if f[2] == "(none)" else f[2], "allowed_ips": f[3],
            "latest_handshake": hs or None, "rx": int(f[5]), "tx": int(f[6]),
            "connected": bool(hs) and now - hs < stale_s,
        })
    return {"ts": float(meta.get("ts", 0)), "ip_forward": meta.get("ip_forward"), "peers": peers}


def wireguard(s: Settings):
    f = Path(s.status_dir) / "wireguard.txt"
    if not f.exists():
        return "down", "no status from vpn-gw", {}
    now = time.time()
    d = parse_wg_dump(f.read_text(), now, s.wg_handshake_stale_s)
    connected = sum(p["connected"] for p in d["peers"])
    if now - d["ts"] > s.status_stale_s:
        return "down", f"status stale ({int(now - d['ts'])}s old)", d
    if d["ip_forward"] == "0":
        return "degraded", "ip_forward=0: tunnels handshake but cannot route (see TKT-003)", d
    return "up", f"{connected}/{len(d['peers'])} peers connected", d


def parse_swanctl_sas(text: str) -> list[dict]:
    """Parse `swanctl --list-sas` output into IKE SAs with remote identity, virtual IP and child count."""
    sas: list[dict] = []
    cur: dict | None = None
    for ln in text.splitlines():
        if ln.startswith("#") or not ln.strip():
            continue
        if not ln.startswith(" ") and ": #" in ln:
            name, rest = ln.split(":", 1)
            state = rest.split(",")[1].strip() if rest.count(",") >= 1 else "UNKNOWN"
            cur = {"name": name, "state": state, "remote_id": None, "remote_addr": None, "vip": None, "children": 0}
            sas.append(cur)
            continue
        if cur is None:
            continue
        s = ln.strip()
        if s.startswith("remote "):
            parts = s.split("'")
            cur["remote_id"] = parts[1] if len(parts) > 2 else None
            tail = parts[-1]
            if "@" in tail:
                cur["remote_addr"] = tail.split("@", 1)[1].strip().split("[")[0].strip()
            if tail.count("[") >= 2:
                cur["vip"] = tail.rsplit("[", 1)[1].rstrip("]").strip()
        elif ", INSTALLED," in s:
            cur["children"] += 1
    return sas


def ipsec(s: Settings):
    f = Path(s.status_dir) / "ipsec.txt"
    if not f.exists():
        return "down", "no status from ipsec-gw", {}
    text = f.read_text()
    ts = float(text.splitlines()[0].split("=", 1)[1]) if text.startswith("# ts=") else 0
    if time.time() - ts > s.status_stale_s:
        return "down", "status stale", {}
    sas = parse_swanctl_sas(text)
    up = [x for x in sas if x["state"] == "ESTABLISHED"]
    return "up", f"{len(up)} IKE SA(s) established", {"sas": sas}


def pki_inventory(s: Settings):
    certs = pki.inventory(s.pki_dir, s.cert_warn_days)
    bad = [c for c in certs if c.status != "up"]
    if any(c.status == "down" for c in certs):
        return "down", f"{len(bad)} cert(s) expired", {"certs": len(certs)}
    if bad:
        return "degraded", f"{len(bad)} cert(s) expire within {s.cert_warn_days}d", {"certs": len(certs)}
    return "up", f"{len(certs)} certificates valid", {"certs": len(certs)}
