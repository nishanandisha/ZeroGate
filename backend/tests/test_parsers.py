import json

from app.probes.files import parse_swanctl_sas, parse_wg_dump
from app.services import traffic

WG = """# ts=1000 ip_forward=1
PRIVKEY\tPUBKEY\t51820\toff
peerAAAAAAAAAAAA\tpsk\t172.30.0.100:33896\t10.99.0.2/32\t990\t1500\t2600\t25
peerBBBBBBBBBBBB\tpsk\t(none)\t10.99.0.3/32\t0\t0\t0\toff
"""

SWAN = """# ts=1
rw-cert: #2, ESTABLISHED, IKEv2, 9df4_i 0bfe_r*
  local  'vpn.zerogate.lab' @ 172.30.0.11[4500]
  remote 'bob@zerogate.lab' @ 172.30.0.101[4500] [10.98.0.1]
  AES_GCM_16-256/PRF_HMAC_SHA2_384/ECP_384
  corp: #2, reqid 1, INSTALLED, TUNNEL, ESP:AES_GCM_16-256
"""


def test_wg_dump():
    d = parse_wg_dump(WG, now=1000, stale_s=180)
    assert d["ip_forward"] == "1"
    assert [p["connected"] for p in d["peers"]] == [True, False]
    assert d["peers"][0]["endpoint"] == "172.30.0.100:33896"
    assert d["peers"][1]["endpoint"] is None


def test_wg_dump_stale_handshake():
    d = parse_wg_dump(WG, now=1000 + 500, stale_s=180)
    assert not any(p["connected"] for p in d["peers"])


def test_swanctl():
    (sa,) = parse_swanctl_sas(SWAN)
    assert sa == {"name": "rw-cert", "state": "ESTABLISHED", "remote_id": "bob@zerogate.lab",
                  "remote_addr": "172.30.0.101", "vip": "10.98.0.1", "children": 1}


def test_squid_mapping():
    base = {"ts": 1.0, "client": "10.20.0.10", "method": "GET", "url": "https://x/", "host": "x", "bytes": 10,
            "sni": "x", "ms": 1}
    assert traffic.from_squid(json.dumps({**base, "user": "carol", "status": 403, "action": "NONE_NONE",
                                          "bump": "-"})).action == "block"
    e = traffic.from_squid(json.dumps({**base, "user": "alice", "status": 200, "action": "TCP_MISS", "bump": "bump"}))
    assert (e.action, e.inspection, e.user) == ("allow", "bump", "alice")
    assert traffic.from_squid(json.dumps({**base, "user": "-", "status": 407, "action": "TCP_DENIED",
                                          "bump": "-"})).user is None
    assert traffic.from_squid("not json") is None
    assert traffic.from_squid(json.dumps({**base, "method": "-", "status": 0, "action": "NONE_NONE"})) is None


def test_mitm_and_stats():
    line = json.dumps({"ts": 2.0, "client": "10.20.0.10", "method": "POST", "host": "h", "url": "https://h/p",
                       "tls": True, "status": 403, "bytes": 5, "action": "dlp-block", "dlp_rules": ["credit_card"]})
    e = traffic.from_mitm(line)
    s = traffic.stats([e])
    assert s["blocked"] == 1 and s["dlp_rules"] == {"credit_card": 1}


def test_tail_lines(tmp_path):
    f = tmp_path / "log"
    f.write_text("".join(f"{i}\n" for i in range(10000)))
    assert traffic.tail_lines(str(f), 3) == ["9997", "9998", "9999"]
    assert traffic.tail_lines(str(tmp_path / "missing"), 3) == []
