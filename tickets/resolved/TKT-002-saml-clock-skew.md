# TKT-002: SSO login fails right after entering the correct password

| Field | Value |
|---|---|
| Severity | P2 |
| Component | IdP / SAML |
| Environment | Private app (Apache mod_auth_mellon) + Keycloak |
| Status | Resolved |
| Scenario | 02-saml-clock-skew |

## 1. Symptom (as reported)
"I type my password, Keycloak accepts it, then the app shows 400 Bad Request. Every user, every time."

## 2. Reproduction
`make break S=02` starts the app with its clock 2 hours ahead (libfaketime).

## 3. Investigation
The login reaches the app's Assertion Consumer Service and dies there:
```
400 https://localhost:8443/mellon/postResponse
```
The IdP is happy. Keycloak logs a successful login for the SAML client:
```
type="LOGIN", realmName="zerogate", clientId="https://localhost:8443/mellon/metadata" ...
```
So the IdP issued an assertion and the SP rejected it. The SP log says why:
```
[auth_mellon:error] NotOnOrAfter in SubjectConfirmationData was in the past.
```
An assertion that is seconds old is "in the past". Compare clocks:
```
host:      2026-11-11T10:58:52Z
keycloak:  2026-11-11T10:58:53Z
saml-app:  2026-11-11T12:58:53Z      <-- 2 hours ahead
```

## 4. Root cause
SAML assertions carry a validity window (`NotBefore` / `NotOnOrAfter`), usually about a minute. The service provider's
clock was 2 hours ahead of the IdP, so every assertion had already expired when it arrived. Passwords, certificates
and network were all fine.

## 5. Fix
Correct the time source on the SP (`chronyc tracking` / `timedatectl` on a real host). In the lab: `make fix S=02`
restarts the app without the injected offset.

## 6. Verification
`testing/e2e/saml_login.py alice` returns `200 https://localhost:8443/` and the page shows the user's groups.

## 7. Prevention / KB notes
* Direction matters. SP **ahead** gives "NotOnOrAfter in the past". SP **behind** gives "NotBefore in the future".
* Monitor NTP offset on IdP and SPs; alert above 30 seconds.
* A small tolerance (30–60 s) is reasonable. Raising it to hours to "fix" this hides the real fault and weakens replay protection.
* Decode the SAMLResponse (base64) and read `IssueInstant` when you cannot get at the SP's logs.
