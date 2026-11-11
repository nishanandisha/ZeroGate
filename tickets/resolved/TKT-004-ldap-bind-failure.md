# TKT-004: All logins fail with a server error after the IdP restarted

| Field | Value |
|---|---|
| Severity | P1 |
| Component | Directory / IdP |
| Environment | Keycloak + OpenLDAP |
| Status | Resolved |
| Scenario | 04-ldap-bind-failure |

## 1. Symptom (as reported)
"After last night's maintenance restart nobody can sign in to anything. Nothing was changed last night."

## 2. Reproduction
`make break S=04` changes the password of Keycloak's LDAP service account, then restarts Keycloak.

## 3. Investigation
Every user fails, with a server error instead of "wrong password":
```
{"error":"unknown_error","error_description":"For more on this error consult the server log."}
```
Keycloak's log names LDAP as the failing dependency:
```
Caused by: javax.naming.AuthenticationException: [LDAP: error code 49 - Invalid Credentials]
```
Error 49 means a bind was refused. Whose bind? The LDAP server log shows it is the **service account**, not the user:
```
conn=1213 op=0 BIND dn="cn=keycloak-svc,ou=services,dc=zerogate,dc=lab" method=128
conn=1213 op=0 RESULT tag=97 err=49
```
Test both identities directly against LDAP:
```
$ ldapwhoami -D cn=keycloak-svc,ou=services,dc=zerogate,dc=lab -w <configured password>
ldap_bind: Invalid credentials (49)
$ ldapwhoami -D uid=dave,ou=people,dc=zerogate,dc=lab -w <user password>
dn:uid=dave,ou=people,dc=zerogate,dc=lab
```
The directory is up and user passwords are right. Only the service account's stored password is wrong.

## 4. Root cause
The service account password was changed in LDAP without updating Keycloak. Nothing broke at the time, because
Keycloak **pools LDAP connections** that were already authenticated. In testing, logins kept working after the
password change and only failed once Keycloak restarted and had to bind again. That is why the outage appeared to
have no cause: the change and the failure were separated in time.

## 5. Fix
Set the account's password back to the value Keycloak holds (or update Keycloak's federation settings to the new
one). `make fix S=04`.

## 6. Verification
A password-grant token request for `dave` returns an `access_token`; OpenLDAP logs `err=0` for the service bind.

## 7. Prevention / KB notes
* "It broke after a restart but we changed nothing" usually means something changed earlier and was masked by a cache or pool.
* Rotate service account passwords as one procedure: change LDAP, change every consumer, restart or test-bind each one.
* Keycloak's admin console has a **Test authentication** button for the LDAP provider. Use it after any rotation.
* Read the bind DN in the LDAP log before assuming users are mistyping passwords. Error 49 on the service DN is a
  different ticket from error 49 on a user DN.
