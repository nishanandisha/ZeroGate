# Operations runbook

## Start, stop, check
| Task | Command |
|---|---|
| First start (PKI, env, build, run) | `make up` |
| Status | `make ps`, console → Overview |
| Stop / wipe | `make down` / `make destroy` |
| Client demo | `make demo` |
| All tests | `make test` |
| Fault injection | `make scenarios`, `make cycle S=03`, `make breakfix` |

## URLs and logins
| What | Where | Login |
|---|---|---|
| Admin console | http://localhost:3300 | `alice` (member of `zg-admins`) |
| Private app (SAML) | https://localhost:8443 | any LDAP user; `/admin` needs `zg-admins` |
| Keycloak admin | http://localhost:8080 | `KEYCLOAK_ADMIN` in `infrastructure/.env` |
| API docs | http://localhost:8800/api/docs | bearer token |

Lab users: `alice` (engineering, zg-admins), `bob` (finance), `carol` (contractors), `dave` (engineering).
Password: `LAB_USER_PASSWORD` in `infrastructure/.env`.
For the browser to trust https://localhost:8443, import `infrastructure/pki/root-ca/root.crt` into your keychain.

## Where to look first
| Symptom | First command | Ticket |
|---|---|---|
| Certificate error through a proxy | `curl -v -x … https://site 2>&1 \| grep -E 'issuer\|problem'` | TKT-001, TKT-007 |
| 400 at `/mellon/postResponse` | `docker logs zerogate-saml-app-1 \| grep auth_mellon` | TKT-002, TKT-006 |
| VPN connected, no traffic | `wg show`; `tcpdump -ni any` on `vpn-gw`; `iptables -t nat -L` | TKT-003 |
| Everyone fails to log in | `docker logs zerogate-openldap-1 \| grep err=49` | TKT-004 |
| IKEv2 fails instantly | `docker logs zerogate-ipsec-gw-1 \| grep proposals` | TKT-005 |
| 407 from the proxy | user/password; then `squid-svc` bind in the LDAP log | – |
| 403 from the proxy | `/var/log/squid/access.log`: which user, which host; check `policy/*.txt` and groups | – |

## Log locations
| Component | Command |
|---|---|
| LDAP binds and searches (with result codes) | `docker logs zerogate-openldap-1` |
| Keycloak login events | `docker logs zerogate-keycloak-1 \| grep org.keycloak.events` |
| SAML SP | `docker logs zerogate-saml-app-1` |
| Squid access (JSON) / internals | `docker exec zerogate-squid-1 tail -f /var/log/squid/access.log` / `cache.log` |
| DLP flows (JSON) | `docker exec zerogate-mitmproxy-1 tail -f /logs/flows.jsonl` |
| IKE negotiation | `docker logs zerogate-ipsec-gw-1`; client: `/var/log/charon.log` |
| WireGuard | `docker exec zerogate-vpn-gw-1 wg show`; firewall: `policy.sh show` |
| API audit | `docker logs zerogate-backend-1` |

## Changing policy
* Block a category for everyone: add the domain to `infrastructure/proxy/squid/policy/cat-gambling.txt`, rebuild `squid`.
* Exempt a site from decryption: add it to `policy/no-inspect.txt`.
* DLP rules: `infrastructure/proxy/mitmproxy/addons/zerogate_dlp.py` (`RULES`).
* Publish another private service to tunnel users: add a rule in `vpn/wireguard/policy.sh` and `vpn/ipsec-strongswan/entrypoint.sh`.

## Known limits (be honest about these)
* Lab-grade secrets and HTTP on Keycloak; private keys sit on disk with loose permissions so containers can read them.
* Keycloak runs in dev mode with an in-container database: recreating the container resets the realm (and its signing keys).
* The proxy is explicit (clients are pointed at it); there is no transparent interception or PAC file.
* Proxy users are identified by Basic auth to LDAP, not by SAML/Kerberos as commercial gateways do.
* OpenLDAP stands in for Active Directory. `infrastructure/identity/samba-ad/README.md` describes the AD variant; it is not built.
* The Windows client scripts and the AWS Terraform are written but have not been run end to end.
