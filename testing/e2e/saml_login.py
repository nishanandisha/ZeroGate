"""Drive a real SP-initiated SAML login like a browser would.

app (mellon) -> Keycloak login form -> LDAP bind -> signed SAMLResponse (HTTP-POST) -> ACS -> protected page.
Usage: python saml_login.py [user] [password] [path]
"""
import html
import os
import pathlib
import re
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parents[2]
CA = str(ROOT / "infrastructure/pki/root-ca/root.crt")
APP = "https://localhost:8443"


class SamlLoginError(Exception):
    pass


def _form(page: str) -> tuple[str, dict]:
    action = re.search(r'<form[^>]*action="([^"]+)"', page)
    if not action:
        raise SamlLoginError("no form in page")
    fields = dict(re.findall(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"', page))
    return html.unescape(action.group(1)), {k: html.unescape(v) for k, v in fields.items()}


def _browser_like(s: requests.Session) -> None:
    # Browsers treat http://localhost as a secure context and send Secure cookies to it; requests does not.
    # Python's cookiejar also refuses "Domain=localhost" cookies for host "localhost" (it calls the host
    # "localhost.local"); browsers accept them. Normalise both quirks.
    for c in list(s.cookies):
        if c.domain.lstrip(".").startswith("localhost"):
            c.secure = False
            if c.domain == ".localhost":
                s.cookies.clear(c.domain, c.path, c.name)
                s.cookies.set(c.name, c.value, domain="localhost.local", path=c.path)


def login(user: str, password: str, path: str = "/") -> requests.Response:
    s = requests.Session()
    s.verify = CA
    r = s.get(APP + path, timeout=15)  # -> 303 mellon/login -> 302 keycloak -> login form
    if "kc-form-login" not in r.text:
        raise SamlLoginError(f"expected Keycloak login form, got {r.status_code} at {r.url}")
    action, _ = _form(r.text)
    _browser_like(s)
    r = s.post(action, data={"username": user, "password": password, "credentialId": ""}, timeout=15)
    if "SAMLResponse" not in r.text:
        err = re.search(r'id="input-error"[^>]*>\s*([^<]+)', r.text)
        raise SamlLoginError("IdP rejected login: " + (err.group(1).strip() if err else f"HTTP {r.status_code}"))
    acs, fields = _form(r.text)
    _browser_like(s)
    r = s.post(acs, data=fields, timeout=15, allow_redirects=False)  # mellon validates assertion, sets session
    if r.status_code not in (302, 303):
        return r  # e.g. 400/401 when the assertion is rejected (clock skew, bad signature, ...)
    _browser_like(s)
    return s.get(r.headers["Location"], timeout=15)


if __name__ == "__main__":
    # The password comes from the command line or LAB_USER_PASSWORD; there is no built-in default.
    args = sys.argv[1:]
    u = args[0] if args else "alice"
    p = args[1] if len(args) > 1 else os.environ.get("LAB_USER_PASSWORD", "")
    path = args[2] if len(args) > 2 else "/"
    if not p:
        sys.exit("usage: saml_login.py [user] [password] [path]  (or set LAB_USER_PASSWORD)")
    resp = login(u, p, path)
    print(resp.status_code, resp.url)
    print(re.sub(r"<[^>]+>", " ", resp.text)[:600])
