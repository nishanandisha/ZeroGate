"""Probes for services reached over the network: LDAP, Keycloak, SAML app, Squid, mitmproxy."""
import socket
import ssl
from pathlib import Path

import httpx
from ldap3 import Connection, Server

from app.core.config import Settings


def _hostport(addr: str) -> tuple[str, int]:
    host, port = addr.rsplit(":", 1)
    return host, int(port)


def ldap(s: Settings):
    conn = Connection(Server(s.ldap_url, connect_timeout=3), s.ldap_bind_dn, s.ldap_bind_password, receive_timeout=3)
    if not conn.bind():
        return "down", f"bind failed: {conn.result.get('description')} ({conn.result.get('message') or 'no message'})", {}
    conn.search(f"ou=people,{s.ldap_base}", "(objectClass=inetOrgPerson)", attributes=["uid"])
    users = len(conn.entries)
    conn.unbind()
    return ("up" if users else "degraded"), f"bind ok as {s.ldap_bind_dn.split(',')[0]}, {users} users", {"users": users}


def keycloak(s: Settings):
    base = f"{s.keycloak_internal_url}/realms/{s.keycloak_realm}"
    with httpx.Client(timeout=4) as c:
        oidc = c.get(f"{base}/.well-known/openid-configuration")
        oidc.raise_for_status()
        saml = c.get(f"{base}/protocol/saml/descriptor")
    issuer = oidc.json().get("issuer")
    data = {"issuer": issuer, "saml_metadata": saml.status_code == 200}
    if issuer != s.keycloak_issuer:
        return "degraded", f"issuer mismatch: {issuer} != {s.keycloak_issuer}", data
    return ("up" if saml.status_code == 200 else "degraded"), f"realm {s.keycloak_realm} OIDC+SAML ok", data


def saml_app(s: Settings):
    ctx = ssl.create_default_context(cafile=str(Path(s.pki_dir) / "root-ca/root.crt"))
    with httpx.Client(timeout=4, verify=ctx) as c:
        r = c.get(s.saml_app_url)
    return ("up" if r.status_code == 200 else "down"), f"healthz {r.status_code}, TLS chain valid", {"status": r.status_code}


def squid(s: Settings):
    host, port = _hostport(s.squid_addr)
    with socket.create_connection((host, port), timeout=3) as sock:
        sock.sendall(b"CONNECT example.com:443 HTTP/1.1\r\nHost: example.com:443\r\n\r\n")
        line = sock.recv(256).split(b"\r\n", 1)[0].decode(errors="replace")
    # An unauthenticated CONNECT must be challenged: that proves auth is enforced
    if " 407 " in f"{line} ":
        return "up", "listening, proxy-auth enforced (407)", {"response": line}
    return "degraded", f"unexpected response to unauthenticated CONNECT: {line!r}", {"response": line}


def mitmproxy(s: Settings):
    host, port = _hostport(s.mitm_addr)
    with socket.create_connection((host, port), timeout=3):
        pass
    return "up", "listening", {}
