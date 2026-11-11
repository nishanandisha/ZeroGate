#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
dc exec -T openldap ldappasswd -x -H ldap://127.0.0.1 -D "cn=admin,dc=zerogate,dc=lab" -w "$LDAP_ADMIN_PW" -s "$LDAP_KC_PW" "cn=keycloak-svc,ou=services,dc=zerogate,dc=lab"
