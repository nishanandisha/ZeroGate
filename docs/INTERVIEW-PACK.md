# Interview pack

## 30-second pitch
"I built a small version of an SSE platform: users connect through WireGuard or IKEv2, web traffic goes through a proxy
that decrypts HTTPS with our own CA and applies per-user and per-group policy from LDAP, and apps use SAML single
sign-on through Keycloak. Then I broke it seven different ways, on purpose, and wrote each one up as a support ticket
with the commands and output that led to the root cause. Every fault is a script, so I can reproduce any of them live."

## 5-minute demo
| Step | Command / click | What it shows |
|---|---|---|
| 1 | Console → Overview | 8 components probed live; traffic counts |
| 2 | `make demo` | tunnel up, app reachable, LDAP port blocked, HTTPS issuer is our Inspection CA |
| 3 | https://localhost:8443 as `bob`, then `/admin` | SAML login from LDAP; 403 because bob is not in `zg-admins` |
| 4 | `make break S=03` → `make diagnose S=03` | handshake fine, pings lost, empty NAT table |
| 5 | `make fix S=03` → Console → Support tickets → TKT-003 | fix and the written-up ticket |

## Which ticket answers which question
| Question | Use |
|---|---|
| "Customer gets SSL errors after enabling inspection" | TKT-001, and TKT-007 for the harder variant |
| "SAML login fails, how do you troubleshoot?" | TKT-002 (time) vs TKT-006 (signature): same symptom, one log line apart |
| "VPN is up but no traffic" | TKT-003 and its six-step checklist |
| "Tell me about a hard problem" | TKT-004: the change and the failure were days apart because of connection pooling |
| "IPsec phase 1 vs phase 2" | TKT-005: where it fails tells you what it is |

## Things found by building it, not by reading
* mitmproxy did not send the intermediate CA until the chain was added to its CA file (became TKT-007).
* Changing an LDAP service password broke nothing until Keycloak restarted (became TKT-004).
* `wg show dump` prints the private key; the status feed was leaking it to other containers until it was redacted.
  There is now a regression test for that.
* Killed VPN daemons stayed as zombie processes and a "is it running?" check counted them.

## Honest scope
See "Known limits" in `docs/runbooks/RUNBOOK.md`. In short: OpenLDAP not AD, explicit proxy not transparent, Basic proxy
auth, lab secrets, Windows and AWS parts written but not run.

## Concepts to be able to explain without notes
SSL-Bump peek / splice / bump · why clients trust only the root · SAML SP-initiated flow, ACS, `NotOnOrAfter`,
audience · OIDC code flow with PKCE, JWKS, `aud` and `iss` checks · LDAP bind vs search, error 49 · IKE_SA_INIT vs
IKE_AUTH vs CHILD_SA · WireGuard AllowedIPs as both routing table and ACL · NAT and the return path.
