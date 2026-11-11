# Roadmap

| Stage | Name | Lead team | Deliverable |
|---|---|---|---|
| 0 | Scaffold | Architecture | Folder structure, charters, roadmap |
| 1 | Architecture | Architecture | Network diagram, IP plan, trust flows, ADRs |
| 2 | PKI | Platform | Root + intermediate CA, proxy signing cert, server certs |
| 3 | Identity | Platform | OpenLDAP (users/groups), Keycloak realm federated to LDAP, SAML client |
| 4 | VPN | Platform | WireGuard gateway + IPsec (strongSwan) gateway, client configs |
| 5 | Inspection proxy | Platform | Squid SSL-Bump + mitmproxy, policy (block categories), access logs |
| 6 | Protected app | Platform | SAML service provider behind VPN and proxy |
| 7 | Clients | Platform | Linux client container; Windows VM guide (VirtualBox) + scripts |
| 8 | Backend | Backend | FastAPI: component health probes, users (LDAP), tickets, proxy logs |
| 9 | Frontend | Frontend | React console: dashboard, traffic, users, tickets |
| 10 | Testing | QA | Integration tests + automated break/fix scenarios |
| 11 | Support tickets | Support | 6+ tickets: CA trust, SAML clock skew, VPN no-traffic, LDAP bind, MTU, cert SAN |
| 12 | Cloud and CI | DevOps | Terraform (AWS free tier), GitHub Actions |
| 13 | Interview pack | All | Demo script, talking points |

All stages are complete. See `docs/status/` for what was verified and what was not.
