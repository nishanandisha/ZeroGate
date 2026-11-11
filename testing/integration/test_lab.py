"""Integration tests against the running lab (make up first). Each test maps to a product claim."""
import jwt
import pytest
import requests
from conftest import API, PW, cexec, curl_code, get_token
from saml_login import login

DLP = "-x http://10.20.0.21:8080"


# ---------- Connect: tunnels + segmentation ----------
@pytest.mark.parametrize("client", ["client-wg", "client-ipsec"])
def test_tunnel_reaches_private_app(client):
    assert cexec(client, "ping -c2 -W2 10.10.0.40").returncode == 0
    assert curl_code(client, "--resolve app.zerogate.lab:443:10.10.0.40 https://app.zerogate.lab/healthz").startswith("200")


@pytest.mark.parametrize("client", ["client-wg", "client-ipsec"])
@pytest.mark.parametrize("target", ["10.10.0.20 389", "10.10.0.30 8080", "10.10.0.50 8000"])
def test_segmentation_blocks_everything_not_published(client, target):
    """Tunnel users may reach the app and the proxies only. Not LDAP, not the IdP backend, not the API."""
    assert cexec(client, f"nc -z -w 3 {target}").returncode != 0


def test_wireguard_handshake_is_recent():
    out = cexec("client-wg", "wg show wg0 latest-handshakes").stdout.split()
    assert int(out[1]) > 0


def test_ipsec_uses_strong_crypto():
    out = cexec("client-ipsec", "swanctl --list-sas").stdout
    assert "ESTABLISHED" in out and "AES_GCM_16-256" in out and "ECP_384" in out


# ---------- Inspect: SWG policy ----------
def issuer(client: str, proxy: str, url: str) -> str:
    return cexec(client, f"curl -sv -o /dev/null --max-time 20 {proxy} {url} 2>&1 | grep -m1 'issuer:'").stdout


def test_https_is_inspected_and_trusted(swg):
    assert curl_code("client-wg", f"{swg('alice')} https://example.com").startswith("200")
    assert "ZeroGate Inspection CA" in issuer("client-wg", swg("alice"), "https://example.com")


def test_privacy_category_is_not_decrypted(swg):
    iss = issuer("client-wg", swg("alice"), "https://example.net")
    assert iss and "ZeroGate" not in iss


def test_proxy_requires_authentication(swg):
    assert curl_code("client-wg", "-x http://10.20.0.20:3128 https://example.com").endswith("/407")
    assert curl_code("client-wg", "-x 'http://alice:wrong-password@10.20.0.20:3128' https://example.com").endswith("/407")


def test_category_block_applies_to_everyone(swg):
    assert curl_code("client-wg", f"{swg('alice')} https://www.bet365.com").startswith("403")


def test_group_policy_contractor_vs_employee(swg):
    """Judge by the gateway's own block marker, not the status code: the site itself may answer 403
    (it does to cloud addresses such as CI runners), which says nothing about our policy."""
    def blocked_by_gateway(user: str) -> bool:
        headers = cexec("client-wg", f"curl -s -o /dev/null -D - --max-time 20 {swg(user)} https://www.reddit.com").stdout
        assert "HTTP/" in headers, f"no response for {user}"
        return "x-squid-error: err_access_denied" in headers.lower()
    assert blocked_by_gateway("carol")
    assert not blocked_by_gateway("dave")


def test_untrusted_client_rejects_inspected_tls(swg):
    """Without the Root CA the client must refuse the re-signed certificate (TKT-001)."""
    r = cexec("client-wg", f": > /tmp/empty.pem; curl -s -o /dev/null --max-time 20 --cacert /tmp/empty.pem --capath /nonexistent "
                           f"{swg('alice')} https://example.com; echo $?")
    assert r.stdout.strip().endswith(("60", "77"))


# ---------- Inspect: DLP ----------
@pytest.mark.parametrize("body,rule", [("card=4111 1111 1111 1111", "credit_card"), ("ssn=123-45-6789", "us_ssn"),
                                       ("key=AKIAIOSFODNN7EXAMPLE", "aws_access_key"), ("doc=ZeroGate Confidential", "classified_marker")])
def test_dlp_blocks_sensitive_uploads(body, rule):
    out = cexec("client-wg", f"curl -s --max-time 20 {DLP} -d '{body}' https://httpbin.org/post").stdout
    assert "ZeroGate DLP" in out and rule in out


def test_dlp_allows_clean_upload():
    assert curl_code("client-wg", f"{DLP} -d 'hello=world' https://httpbin.org/post").startswith("200")


# ---------- Identify: SAML + OIDC + LDAP ----------
def test_saml_login_carries_ldap_groups():
    r = login("alice", PW, "/")
    assert r.status_code == 200 and "engineering;zg-admins" in r.text


def test_saml_group_authorisation():
    assert login("alice", PW, "/admin").status_code == 200
    assert login("bob", PW, "/admin").status_code == 403


def test_saml_rejects_bad_password():
    from saml_login import SamlLoginError
    with pytest.raises(SamlLoginError, match="IdP rejected"):
        login("alice", "wrong-password", "/")


def test_token_claims_come_from_ldap():
    claims = jwt.decode(get_token("carol"), options={"verify_signature": False})
    assert claims["groups"] == ["contractors"] and "zerogate-api" in claims["aud"]


# ---------- Control plane ----------
def test_api_requires_token_and_admin_group():
    assert requests.get(f"{API}/me", timeout=10).status_code == 401
    assert requests.get(f"{API}/me", headers={"Authorization": f"Bearer {get_token('bob')}"}, timeout=10).status_code == 403


def test_all_components_healthy(admin_headers):
    comps = requests.get(f"{API}/health/components", headers=admin_headers, timeout=30).json()
    assert len(comps) == 8
    assert {c["id"]: c["status"] for c in comps if c["status"] != "up"} == {}


def test_traffic_log_attributes_requests_to_users(admin_headers, swg):
    curl_code("client-wg", f"{swg('dave')} https://example.com")
    events = requests.get(f"{API}/traffic/events?limit=100&user=dave", headers=admin_headers, timeout=15).json()
    assert any(e["host"] == "example.com" and e["inspection"] == "bump" for e in events)


def test_status_feed_contains_no_key_material(admin_headers):
    """Regression: the WireGuard status dump once exposed the private key and PSKs."""
    out = cexec("vpn-gw", "cat /status/wireguard.txt; cat /config/server_private.key").stdout.splitlines()
    private_key, status = out[-1], "\n".join(out[:-1])
    assert private_key not in status and "(hidden)" in status


def test_tickets_and_scenarios_are_linked(admin_headers):
    tickets = requests.get(f"{API}/tickets", headers=admin_headers, timeout=10).json()
    scenarios = {s["id"] for s in requests.get(f"{API}/scenarios", headers=admin_headers, timeout=10).json()}
    assert len(tickets) >= 7 and {t["scenario"] for t in tickets} <= scenarios
