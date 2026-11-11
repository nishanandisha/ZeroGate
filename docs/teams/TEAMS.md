# Team Charters

| Team | Owns | Folders |
|---|---|---|
| Architecture | System design, network plan, trust model, ADRs | `docs/architecture/` |
| Platform / Infra | PKI, VPN, proxy, identity, Docker Compose, Terraform | `infrastructure/`, `scripts/` |
| Backend | Control-plane API, health probes, ticket and log APIs | `backend/` |
| Frontend | Admin console UI | `frontend/` |
| QA / Testing | Integration tests, break-fix scenarios, test reports | `testing/` |
| Support (TAC) | Ticket write-ups, runbooks | `tickets/`, `docs/runbooks/` |
| DevOps | CI, linting, release | `.github/` |

Every stage ends with a status report in `docs/status/STAGE-XX.md`.
