# Stages 9–13 status ✅

| Stage | Result | Evidence |
|---|---|---|
| 9 Frontend | React console with OIDC (PKCE) login: Overview, Traffic, Directory, Certificates, Support tickets | Logged in through Keycloak in a browser; Overview, Traffic and Support tickets checked on screen. Directory and Certificates pages compile and their APIs return data, but were not opened in the browser |
| 10 Testing | 16 backend unit tests, 30 integration tests, 7 break/fix cycles | `make test`, `make breakfix` → `testing/reports/break-fix-report.md` |
| 11 Tickets | 7 tickets written from captured output | `tickets/resolved/`, evidence in `testing/reports/evidence/` |
| 12 Cloud and CI | Terraform for AWS; GitHub Actions with 4 jobs | `terraform validate` passes. Not applied to AWS. The workflow has not run on GitHub |
| 13 Interview pack | Pitch, demo script, question → ticket map | `docs/INTERVIEW-PACK.md` |

Not done: Windows VM (scripts written, not run), Samba-AD variant (documented only), separate metrics stack.
