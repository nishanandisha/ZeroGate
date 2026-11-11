# ZeroGate test metrics

Measured on 2026-11-11 against the running lab (11 containers, Docker Desktop, Apple Silicon).
Reproduce with `make test` and `make breakfix`.

## Summary

| Suite | Cases | Passed | Failed | Pass rate | Run time |
|---|---|---|---|---|---|
| Backend unit tests | 16 | 16 | 0 | 100% | 0.9 s |
| Integration tests (live lab) | 30 | 30 | 0 | 100% | 28 s |
| Leak and exposure tests (`make security`) | 20 | 20 | 0 | 100% | 2.8 s |
| Break/fix scenarios | 7 | 7 | 0 | 100% | 2 min 5 s |
| **Total** | **73** | **73** | **0** | **100%** | about 2 min 37 s |

Static checks, all clean: ruff (backend and the security tests), TypeScript type-check and production
build (frontend). Shellcheck, `docker compose config`, `terraform fmt` and `terraform validate` were clean
on the earlier run of this date and were not repeated after the last changes.

Stability: the integration suite was run six times on this date, three of them straight after a full
fault-injection pass. All six runs were 30 of 30, with no flaky test.

## Backend unit tests

| File | Cases | What it covers |
|---|---|---|
| `test_parsers.py` | 8 | Squid and mitmproxy log parsing, WireGuard and IPsec status parsing |
| `test_security.py` | 4 | Token validation: valid, wrong key, wrong audience or issuer, missing group |
| `test_api.py` | 4 | Public endpoints, auth enforcement, certificate inventory |

Line coverage of `backend/app` from the unit tests alone: **about 73%** (380 of 521 executable lines),
measured with Python's built-in `trace` module.

| Module | Lines | Covered |
|---|---|---|
| `core/config.py`, `main.py`, `schemas/models.py` | 121 | 100% |
| `services/pki.py` | 29 | 93% |
| `core/security.py` | 47 | 91% |
| `api/routes/health.py` | 24 | 91% |
| `services/traffic.py` | 65 | 90% |
| `probes/files.py` | 79 | 62% |
| `api/routes/admin.py` | 44 | 59% |
| `services/content.py` | 27 | 37% |
| `probes/base.py` | 12 | 33% |
| `probes/network.py` | 47 | 27% |
| `services/directory.py` | 26 | 26% |

The low-coverage modules are the ones that talk to live services (LDAP, TCP and HTTP probes). The unit
tests do not mock them. They are exercised by the integration suite instead, which is not counted in
the 73%.

## Integration tests by area

| Area | Cases | Examples |
|---|---|---|
| VPN and segmentation | 11 | Both tunnels reach the private app; 6 unpublished ports are blocked; IPsec uses AES-GCM-256; status feed leaks no keys |
| Web inspection and DLP | 12 | HTTPS is decrypted and trusted; proxy needs a login; contractor vs employee policy; 4 sensitive-upload patterns blocked; privacy category not decrypted |
| Identity and SSO | 4 | SAML login carries LDAP groups; bad password rejected; `/admin` limited by group; token claims come from LDAP |
| Control plane | 3 | All 8 health probes green; API needs a token and the admin group; every ticket links to a scenario |

Slowest cases: the three WireGuard segmentation checks (3.2 to 3.5 s each, because a blocked port is
confirmed by waiting for a timeout) and the SAML group test (2.6 s).

## Leak and exposure tests

`testing/security/test_no_leaks.py`, 20 cases, run against the live lab and the working tree.

| Area | Cases | What it proves |
|---|---|---|
| Repository | 4 | Nothing git would publish is a key, `.env`, state file or generated PKI/VPN material; no file contains a live password, private key, token-shaped string or local home path; `.env.example` holds placeholders only |
| API | 12 | Only `/api/health/live` and `/api/auth/config` answer without a token; missing, garbage and `alg: none` tokens get 401 on every other route; a valid non-admin gets 403 everywhere; no write methods; admin responses contain no passwords, keys, tokens or sensitive field names; errors show no stack traces or file contents; CORS rejects foreign origins; responses are `no-store` |
| Console | 4 | nginx serves no dotfiles, keys or config; the JS bundle has no secrets and no source maps; security headers are set; the `/api` proxy enforces auth too |

## Break/fix scenarios

Each cycle is: baseline check, inject the fault, confirm the check now fails, capture evidence, apply
the fix, confirm recovery. Times are whole seconds. Evidence files are passed through a redaction filter
(passwords and local paths) before they are written.

| Scenario | Ticket | Result | Inject | Detect | Fix | Verify after fix | Whole cycle |
|---|---|---|---|---|---|---|---|
| 01 CA not trusted | TKT-001 | PASS | 0 | 0 | 0 | 1 | 3 |
| 02 SAML clock skew | TKT-002 | PASS | 12 | 2 | 12 | 4 | 32 |
| 03 VPN up, no traffic | TKT-003 | PASS | 0 | 4 | 0 | 2 | 15 |
| 04 LDAP bind failure | TKT-004 | PASS | 23 | 1 | 0 | 1 | 26 |
| 05 IPsec proposal mismatch | TKT-005 | PASS | 2 | 0 | 4 | 1 | 10 |
| 06 IdP key rotation | TKT-006 | PASS | 5 | 1 | 12 | 1 | 24 |
| 07 Missing intermediate | TKT-007 | PASS | 7 | 0 | 5 | 0 | 15 |

- Fault detection rate: 7 of 7 (every injected fault made its check fail).
- Recovery rate: 7 of 7 (every fix restored the check).
- Mean time to detect: 1.1 s. Mean time to restore (fix plus verification): 6.1 s.

These are script timings, not human response times: the fault and the fix are already known. They show
that each ticket is reproducible and how long a demo of it takes.

## Not covered by any test

- Frontend: no component or browser tests. The five console pages were checked by hand in Chrome and
  captured as screenshots in `docs/screenshots/`.
- Windows client PowerShell scripts: never run.
- AWS Terraform: validated only, never applied.
- GitHub Actions workflow: never run.
- Load, performance and concurrency: not tested.
