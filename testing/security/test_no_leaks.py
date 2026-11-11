"""Leak and exposure checks. Run with `make security` (the lab must be up).

Three questions:
  1. Repository: would `git add` pick up a private key, a real password or a machine-specific path?
  2. API: does every route enforce authentication and the admin group, and do responses stay free of secrets?
  3. Console: does the web server hand out secrets, dotfiles, source maps, or miss its security headers?
"""
import json
import pathlib
import re
import subprocess

import pytest
import requests

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENV = dict(line.split("=", 1) for line in (ROOT / "infrastructure/.env").read_text().splitlines()
           if "=" in line and not line.startswith("#"))
# Live secret values to hunt for. Untouched "change-me-..." placeholders are public by design, so they are skipped.
SECRETS = {k: v for k, v in ENV.items() if "PASSWORD" in k and v and not v.startswith("change-me")}
API = "http://localhost:8800"
CONSOLE = "http://localhost:3300"
KC_TOKEN = "http://localhost:8080/realms/zerogate/protocol/openid-connect/token"
PUBLIC_ROUTES = {"/api/health/live", "/api/auth/config"}  # the only routes that may answer without a token

PRIVATE_KEY = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
TOKEN_SHAPES = re.compile(r"AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9_-]{24,}|xox[abprs]-[A-Za-z0-9-]{10,}"
                          r"|AIza[0-9A-Za-z_-]{35}|eyJ[A-Za-z0-9_-]{20,}\.eyJ[A-Za-z0-9_-]{20,}\.")
SENSITIVE_FIELDS = re.compile(r"passw|secret|private|credential|userpassword|bind_?pw|psk|preshared", re.I)
KNOWN_DUMMIES = ["AKIAIOSFODNN7EXAMPLE"]  # AWS's documented example key, used as DLP test data
FORBIDDEN_FILES = re.compile(r"(^|/)\.env$|\.(key|pem|p12|pfx|psk|jks|tfstate|tfvars)$|private", re.I)


def token(user: str) -> str:
    r = requests.post(KC_TOKEN, timeout=15, data={"grant_type": "password", "client_id": "zerogate-cli",
                                                  "username": user, "password": ENV["LAB_USER_PASSWORD"]})
    r.raise_for_status()
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin():
    return {"Authorization": f"Bearer {token('alice')}"}


@pytest.fixture(scope="session")
def routes():
    """Every GET route the API declares, with path parameters filled in."""
    spec = requests.get(f"{API}/api/openapi.json", timeout=10).json()
    return sorted(re.sub(r"\{[^}]+\}", "TKT-001", p) for p, ops in spec["paths"].items() if "get" in ops)


@pytest.fixture(scope="session")
def protected(routes):
    return [r for r in routes if r not in PUBLIC_ROUTES]


def assert_clean(text: str, where: str):
    for name, value in SECRETS.items():
        assert value not in text, f"{where}: contains the value of {name}"
    assert not PRIVATE_KEY.search(text), f"{where}: contains a private key"
    assert not TOKEN_SHAPES.search(text), f"{where}: contains something shaped like an API key or token"


def field_names(obj, found=None):
    found = set() if found is None else found
    if isinstance(obj, dict):
        for k, v in obj.items():
            found.add(str(k))
            field_names(v, found)
    elif isinstance(obj, list):
        for v in obj:
            field_names(v, found)
    return found


# ---------- 1. Repository ----------
def candidate_files() -> list[str]:
    """Files git tracks plus files it would add: exactly what a push can publish."""
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                         capture_output=True, text=True, check=True).stdout
    return [f for f in out.split("\0") if f and (ROOT / f).is_file()]


def test_repo_has_no_secret_files():
    bad = [f for f in candidate_files() if FORBIDDEN_FILES.search(f)]
    assert not bad, f"secret-bearing files are not git-ignored: {bad}"


def test_repo_has_no_generated_key_material():
    bad = [f for f in candidate_files() if f.startswith(("infrastructure/pki/root-ca/", "infrastructure/pki/intermediate-ca/",
                                                         "infrastructure/pki/issued/", "infrastructure/vpn/wireguard/config/"))]
    assert not bad, f"generated PKI / VPN material would be committed: {bad}"


def test_repo_contents_have_no_secrets_or_local_paths():
    home = str(pathlib.Path.home())
    this_file = str(pathlib.Path(__file__).resolve().relative_to(ROOT))
    problems = []
    for f in candidate_files():
        if f == this_file or f.endswith(("package-lock.json", ".png", ".jpg", ".ico")):
            continue
        text = (ROOT / f).read_text(errors="ignore")
        for dummy in KNOWN_DUMMIES:
            text = text.replace(dummy, "")
        problems += [f"{f}: value of {n}" for n, v in SECRETS.items() if v in text]
        problems += [f"{f}: private key"] if PRIVATE_KEY.search(text) else []
        problems += [f"{f}: token-shaped string"] if TOKEN_SHAPES.search(text) else []
        problems += [f"{f}: local home path"] if home in text else []
    assert not problems, "\n".join(problems)


def test_env_example_has_only_placeholders():
    text = (ROOT / ".env.example").read_text()
    for line in text.splitlines():
        if "PASSWORD=" in line and not line.startswith("#"):
            assert line.split("=", 1)[1].startswith("change-me"), f".env.example carries a real-looking password: {line.split('=')[0]}"
    for name, value in SECRETS.items():
        assert value not in text, f".env.example contains the live value of {name}"


# ---------- 2. API ----------
def test_only_expected_routes_are_public(routes):
    open_routes = {r for r in routes if requests.get(API + r, timeout=10).status_code == 200}
    assert open_routes == PUBLIC_ROUTES, f"unexpected unauthenticated routes: {open_routes - PUBLIC_ROUTES}"


def test_missing_token_is_rejected(protected):
    assert protected, "no protected routes discovered"
    for r in protected:
        res = requests.get(API + r, timeout=10)
        assert res.status_code == 401, f"{r} answered {res.status_code} without a token"


@pytest.mark.parametrize("bad", ["garbage", "eyJhbGciOiJub25lIn0.eyJzdWIiOiJhbGljZSIsImdyb3VwcyI6WyJ6Zy1hZG1pbnMiXX0."],
                         ids=["garbage", "alg-none-forgery"])
def test_forged_token_is_rejected(protected, bad):
    for r in protected:
        res = requests.get(API + r, headers={"Authorization": f"Bearer {bad}"}, timeout=10)
        assert res.status_code == 401, f"{r} accepted a forged token ({res.status_code})"


def test_non_admin_is_forbidden_everywhere(protected, admin):
    users = requests.get(f"{API}/api/directory/users", headers=admin, timeout=10).json()
    outsider = next(u["uid"] for u in users if "zg-admins" not in u["groups"])
    headers = {"Authorization": f"Bearer {token(outsider)}"}
    for r in protected:
        res = requests.get(API + r, headers=headers, timeout=10)
        assert res.status_code == 403, f"{r} answered {res.status_code} to non-admin {outsider}"


def test_write_methods_are_not_exposed(routes, admin):
    for r in routes:
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            res = requests.request(method, API + r, headers=admin, timeout=10)
            assert res.status_code in (401, 403, 405), f"{method} {r} answered {res.status_code}"


def test_admin_responses_carry_no_secrets(routes, admin):
    """Even a fully authorised admin must never be sent a password, key or token."""
    for r in routes:
        res = requests.get(API + r, headers=admin, timeout=20)
        assert res.status_code == 200, f"{r}: {res.status_code}"
        assert_clean(res.text, r)
        leaked = {f for f in field_names(res.json()) if SENSITIVE_FIELDS.search(f)}
        assert not leaked, f"{r} returns sensitive-looking fields: {leaked}"


def test_directory_returns_only_the_declared_fields(admin):
    users = requests.get(f"{API}/api/directory/users", headers=admin, timeout=10).json()
    assert users
    for u in users:
        assert set(u) <= {"uid", "name", "email", "title", "groups"}, f"unexpected user fields: {set(u)}"


def test_errors_do_not_leak_internals(admin):
    probes = [("/api/tickets/..%2f..%2f..%2fetc%2fpasswd", admin), ("/api/tickets/%00", admin),
              ("/api/traffic/events?limit=abc", admin), ("/api/traffic/events?limit=99999999", admin),
              ("/api/does-not-exist", admin), ("/api/me", {"Authorization": "Bearer x.y.z"})]
    for path, headers in probes:
        res = requests.get(API + path, headers=headers, timeout=10)
        assert res.status_code in (401, 404, 422), f"{path}: {res.status_code}"
        assert not re.search(r"Traceback|File \"/|root:x:0:0|site-packages", res.text), f"{path} leaks internals"
        assert_clean(res.text, path)


def test_public_config_exposes_only_login_settings():
    cfg = requests.get(f"{API}/api/auth/config", timeout=10).json()
    assert set(cfg) == {"enabled", "authority", "client_id", "admin_group"}
    assert cfg["enabled"] is True, "authentication is switched off"
    assert_clean(json.dumps(requests.get(f"{API}/api/openapi.json", timeout=10).json()), "openapi.json")


def test_cors_does_not_trust_foreign_origins():
    res = requests.get(f"{API}/api/auth/config", headers={"Origin": "https://evil.example"}, timeout=10)
    assert res.headers.get("access-control-allow-origin") not in ("*", "https://evil.example")
    assert res.headers.get("access-control-allow-credentials") != "true"


def test_api_responses_are_not_cacheable(admin):
    res = requests.get(f"{API}/api/directory/users", headers=admin, timeout=10)
    assert res.headers.get("cache-control") == "no-store"
    assert res.headers.get("x-content-type-options") == "nosniff"


# ---------- 3. Console (nginx + built bundle) ----------
def test_console_does_not_serve_secret_files():
    index = requests.get(CONSOLE + "/", timeout=10).text
    for path in ("/.env", "/.git/config", "/.git/HEAD", "/infrastructure/.env", "/pki/root-ca/root.key",
                 "/config.json", "/.DS_Store", "/package.json", "/nginx.conf"):
        res = requests.get(CONSOLE + path, timeout=10)
        # the single-page app answers unknown paths with its own index.html; anything else is a real file
        assert res.status_code == 404 or res.text == index, f"{path} is served by the console"
        assert_clean(res.text, path)


def test_console_bundle_has_no_secrets_or_source_maps():
    index = requests.get(CONSOLE + "/", timeout=10).text
    assets = re.findall(r'(?:src|href)="(/assets/[^"]+)"', index)
    assert assets, "no bundle found in index.html"
    home = requests.get(CONSOLE + "/", timeout=10).text
    for a in assets:
        body = requests.get(CONSOLE + a, timeout=20).text
        assert_clean(body, a)
        assert "sourceMappingURL" not in body, f"{a} references a source map"
        maybe_map = requests.get(CONSOLE + a + ".map", timeout=10)
        assert maybe_map.status_code == 404 or maybe_map.text == home, f"{a}.map is published"


def test_console_security_headers():
    h = requests.get(CONSOLE + "/", timeout=10).headers
    assert h.get("X-Frame-Options") == "DENY"
    assert h.get("X-Content-Type-Options") == "nosniff"
    assert h.get("Referrer-Policy") == "no-referrer"
    assert "default-src 'self'" in h.get("Content-Security-Policy", "")
    assert not re.search(r"nginx/\d", h.get("Server", "")), "server version is advertised"


def test_console_proxy_enforces_auth_too(protected):
    for r in protected:
        assert requests.get(CONSOLE + r, timeout=10).status_code == 401, f"{r} is open through the console proxy"
