# TKT-006: SSO to one app broke overnight; the admin console still works

| Field | Value |
|---|---|
| Severity | P2 |
| Component | IdP / SAML |
| Environment | Private app (SAML) + Keycloak |
| Status | Resolved |
| Scenario | 06-idp-key-rotation |

## 1. Symptom (as reported)
"The internal app rejects every login with 400 Bad Request since this morning. The admin console logs in fine."

## 2. Reproduction
`make break S=06` adds a new, higher-priority signing key to the Keycloak realm (a key rotation).

## 3. Investigation
Same place as TKT-002: the app's ACS rejects the response.
```
400 https://localhost:8443/mellon/postResponse
```
But the reason in the SP log is different. Not time, signature:
```
[auth_mellon:error] Error processing authn response. Lasso error: [-111] Failed to verify signature.,
  SAML Response: StatusCode1="urn:oasis:names:tc:SAML:2.0:status:Success"
```
The IdP says Success, and the SP cannot verify who signed it. Compare the signing certificates the app has on file
with what the IdP publishes now (SHA-256 fingerprints):
```
App's cached IdP metadata:        IdP metadata now:
  54:C1:C8:E1:...                   31:EA:33:70:...   <-- new, not known to the app
  AC:B4:08:02:...                   54:C1:C8:E1:...
  E4:45:4F:B8:...                   AC:B4:08:02:...
                                    E4:45:4F:B8:...
```

## 4. Root cause
The IdP rotated its signing key and now signs with a key the app has never seen. The app loaded the IdP's metadata
once at start-up and never refreshed it. The admin console was unaffected because it uses OIDC and fetches the
current keys from the JWKS endpoint by key ID on demand.

## 5. Fix
Refresh the SP's copy of the IdP metadata. In the lab the app downloads it on start, so `make fix S=06` restarts it.

## 6. Verification
SAML login returns 200; the app's start-up log prints the new IdP fingerprint.

## 7. Prevention / KB notes
* TKT-002 and this ticket look identical to the user (400 at the ACS). The SP log line separates them in seconds:
  `NotOnOrAfter` → clocks, `Failed to verify signature` → keys or metadata.
* Rotation needs an overlap: publish the new key in metadata first, let SPs refresh, then start signing with it.
* Prefer SPs that refresh metadata from a URL on a schedule over a file pasted in once.
* "One app broken, others fine" after an IdP change points at that app's stored copy of something.
