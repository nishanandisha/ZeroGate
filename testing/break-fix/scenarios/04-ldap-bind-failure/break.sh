#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
dc exec -T openldap ldappasswd -x -H ldap://127.0.0.1 -D "cn=admin,dc=zerogate,dc=lab" -w "$LDAP_ADMIN_PW" -s "rotated-by-someone-$RANDOM" "cn=keycloak-svc,ou=services,dc=zerogate,dc=lab"
# The change is invisible while Keycloak still holds authenticated pooled connections.
# A restart (patch night) forces a fresh bind and exposes it.
dc restart keycloak >/dev/null 2>&1; wait_healthy keycloak 90
