# ZeroGate Architecture

## 1. Goal
Copy, at lab scale, the three things a Security Service Edge (SSE) platform does:
1. **Connect**: users reach private apps only through an authenticated tunnel (WireGuard or IPsec IKEv2).
2. **Inspect**: all web traffic goes through a proxy that decrypts TLS with a company CA, applies
   user and group policy, logs the traffic and re-encrypts it.
3. **Identify**: one directory (OpenLDAP) is the source of truth. Keycloak federates it and provides
   SAML SSO to apps and OIDC to the admin console. The proxy authenticates users against the same directory.

## 2. Topology

```
                         ┌──────────────────────── public / underlay 172.30.0.0/24 ("the internet") ───────────────┐
                         │                                                                                          │
   client-wg 172.30.0.100 ──(WireGuard UDP/51820)──► vpn-gw 172.30.0.10                                             │
   client-ipsec 172.30.0.101 ──(IKEv2 UDP/500,4500)──► ipsec-gw 172.30.0.11                                         │
   Windows VM (VirtualBox) ──► host published ports 51820/udp, 500/udp, 4500/udp                                    │
                         └──────────────────────────────────────────────────────────────────────────────────────────┘
                                     │ tunnel 10.99.0.0/24 (wg)       │ tunnel 10.98.0.0/24 (ipsec pool)
                                     ▼                                ▼
   ┌──────────── edge / DMZ 10.20.0.0/24 ─────────────────────────────────────────────┐
   │ vpn-gw .10   ipsec-gw .11   squid .20 (3128, SSL-Bump + LDAP auth)               │──► real internet (NAT)
   │                             mitmproxy .21 (8080, DLP + JSON flow log)            │
   └──────────────────────────────────────────────────────────────────────────────────┘
                                     │
   ┌──────────── corp 10.10.0.0/24 ───────────────────────────────────────────────────┐
   │ vpn-gw .10  ipsec-gw .11  openldap .20  squid .21  keycloak .30                  │
   │ saml-app .40  backend .50  frontend .60                                          │
   └──────────────────────────────────────────────────────────────────────────────────┘
```

## 3. IP plan

| Host | public 172.30.0.0/24 | edge 10.20.0.0/24 | corp 10.10.0.0/24 | Published to the Mac |
|---|---|---|---|---|
| vpn-gw (WireGuard) | .10 | .10 | .10 | 51820/udp |
| ipsec-gw (strongSwan) | .11 | .11 | .11 | 500/udp, 4500/udp |
| squid | – | .20 | .21 | – (reachable only through a tunnel) |
| mitmproxy | – | .21 | – | – |
| openldap | – | – | .20 | – |
| keycloak | – | – | .30 | 8080 (browser SSO) |
| saml-app (Apache + mod_auth_mellon) | – | – | .40 | 8443 |
| backend (FastAPI) | – | – | .50 | 8800 |
| frontend (nginx + React) | – | – | .60 | 3300 |
| client-wg | .100 | – | – | – |
| client-ipsec | .101 | – | – | – |

Tunnel networks: WireGuard `10.99.0.0/24` (gateway .1, client .2), IPsec virtual-IP pool `10.98.0.0/24`.
Clients run in **split tunnel** mode: only `10.10.0.0/24` and `10.20.0.0/24` go through the tunnel, and web traffic is sent to the proxy.

## 4. Trust model (PKI)

```
ZeroGate Root CA (offline, 10y)
├── ZeroGate Issuing CA (5y)        → server certs: keycloak, saml-app, ipsec-gw, ipsec clients
└── ZeroGate Inspection CA (3y)     → loaded into Squid and mitmproxy, mints leaf certs on the fly
```
Clients trust **only the Root**. Each intermediate is sent in the chain, so a client that lacks the root
fails in a predictable way (TKT-001).

## 5. Key flows

**A. Private app with SAML SSO**
client → tunnel → `https://saml-app` → mellon has no session → 302 to Keycloak `/protocol/saml` →
Keycloak checks the password against LDAP (federation, READ_ONLY) → signed SAML Response POSTed to the ACS `/mellon/postResponse` →
mellon validates the signature, `NotBefore`/`NotOnOrAfter` and the audience → session → app shows the user and groups.

**B. Internet browsing with inspection**
client → tunnel → `CONNECT example.com:443` to squid with `Proxy-Authorization` → squid `basic_ldap_auth` →
group lookup `ext_ldap_group_acl` → policy (block, splice or bump) → bump: squid mints `CN=example.com` signed by the
Inspection CA → the client validates the chain up to the Root → the access log records user, URL and bump action.

**C. Admin console**
browser → React console → OIDC Authorization Code + PKCE against Keycloak (`zerogate-console`) → access token →
FastAPI checks the JWT signature against the realm JWKS, checks `iss` and `aud`, and requires the `zg-admins` group.

## 6. Architecture Decision Records

| ADR | Decision | Why |
|---|---|---|
| 001 | Docker Compose rather than full VMs for the core lab | Apple Silicon host. Each service is reproducible and one `make up` builds the whole lab. The Windows client stays a real VM. |
| 002 | OpenLDAP rather than AD for the core, with a Samba-AD guide | AD needs a Windows Server licence and x86. LDAP binds, filters and groups are the same skills. |
| 003 | Two VPNs: WireGuard and IPsec IKEv2 | WireGuard is modern and simple. IKEv2 with certificates is what enterprise and Windows-native clients use, and it fails in different ways (proposals, certs, NAT-T). |
| 004 | Two inspection engines: Squid and mitmproxy | Squid stands for the production SWG (auth, policy, SSL-Bump). mitmproxy stands for the deep-inspection lane, with a scriptable DLP addon and JSON flow logs. |
| 005 | Keycloak with SAML for apps and OIDC for the console | Matches how SSE vendors federate customer IdPs and how their own admin portals authenticate. |
| 006 | Separate Inspection CA | Limits blast radius. It can be revoked or rotated without re-issuing server certs. |
| 007 | NAT (MASQUERADE) on VPN gateways | Corp hosts need no return routes. User identity comes from proxy authentication, not the source IP. |
| 008 | Fault injection as code (`testing/break-fix`) | Every support ticket can be reproduced: `break.sh`, `verify.sh` (fails), `fix.sh`, `verify.sh` (passes). |
