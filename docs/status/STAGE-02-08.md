# Stages 2–8 status ✅

| Stage | Result | Evidence |
|---|---|---|
| 2 PKI | Root → Issuing CA + Inspection CA → 7 leaf certs | `scripts/pki.sh`, `openssl verify` OK |
| 3 Identity | OpenLDAP (4 users, 4 groups, 3 service accounts, ACLs) federated into Keycloak realm `zerogate` | password grant for `alice` returns groups `engineering, zg-admins` |
| 4 VPN | WireGuard and IPsec IKEv2 (certificate auth, AES-GCM-256/ECP-384), default-deny segmentation on both | ping to corp OK, LDAP port blocked from the tunnel |
| 5 Inspection | Squid SSL-Bump with LDAP auth and group policy; mitmproxy with DLP rules | bump/splice/403/407 matrix and DLP block verified |
| 6 Private app | Apache + mod_auth_mellon SAML SP, `/admin` limited to `zg-admins` | `testing/e2e/saml_login.py`: alice 200, bob 403 |
| 7 Clients | Linux client image (`zg up/status/test`), Windows PowerShell kit | `zg test` all green. Windows scripts are written but not run (no Windows VM yet) |
| 8 Backend | FastAPI: 8 health probes, directory, traffic, PKI, tickets, JWT auth | 16 unit tests pass; live API returns 8/8 components up |

Issues found and fixed on the way: swanctl one-line blocks, stale `charon.vici` socket after restart, mitmproxy not sending
the intermediate CA, Apache cgid under the event MPM, WireGuard status dump exposing key material (now redacted),
host ports 3000/8000 in use by another project (ZeroGate uses 3300/8800).
