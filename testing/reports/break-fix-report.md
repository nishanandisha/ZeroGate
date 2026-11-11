# Break/fix report

Run: 2026-11-11T16:43:09Z

| Scenario | Result | Inject (s) | Detect (s) | Fix (s) | Verify after fix (s) | Cycle (s) |
|---|---|---|---|---|---|---|
| 01-ca-not-trusted | PASS | 0 | 0 | 0 | 1 | 3 |
| 02-saml-clock-skew | PASS | 12 | 2 | 12 | 4 | 32 |
| 03-vpn-up-no-traffic | PASS | 0 | 4 | 0 | 2 | 15 |
| 04-ldap-bind-failure | PASS | 23 | 1 | 0 | 1 | 26 |
| 05-ipsec-proposal-mismatch | PASS | 2 | 0 | 4 | 1 | 10 |
| 06-idp-key-rotation | PASS | 5 | 1 | 12 | 1 | 24 |
| 07-missing-intermediate | PASS | 7 | 0 | 5 | 0 | 15 |
