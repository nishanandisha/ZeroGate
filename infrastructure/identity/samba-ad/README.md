# Active Directory variant (not built)

The lab uses OpenLDAP. To practise against AD semantics, replace it with a Samba AD domain controller or a Windows
Server evaluation VM. What changes:

| Setting | OpenLDAP (built) | Active Directory |
|---|---|---|
| User naming attribute | `uid` | `sAMAccountName` / `userPrincipalName` |
| User object class | `inetOrgPerson` | `user` |
| Group membership | `member` on `groupOfNames` | `member` + `memberOf`; nested groups via `1.2.840.113556.1.4.1941` |
| UUID attribute | `entryUUID` | `objectGUID` |
| Bind | simple bind over 389 | LDAPS 636 or StartTLS required for password operations |
| Keycloak vendor | `other` | `ad` (enables the MSAD account-control mapper) |
| Squid helper filter | `uid=%s` | `sAMAccountName=%s` |

Extra failure modes AD adds: account lockout and `userAccountControl` flags (error 49 sub-codes `52e`, `775`, `532`),
Kerberos clock skew (5 minutes), and LDAP channel binding / signing requirements.
