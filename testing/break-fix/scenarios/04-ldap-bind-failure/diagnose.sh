#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
run sh -c "curl -s --max-time 10 -d grant_type=password -d client_id=zerogate-cli -d username=dave --data-urlencode 'password=$LAB_PW' http://localhost:8080/realms/zerogate/protocol/openid-connect/token"
run sh -c "docker logs --since 2m zerogate-keycloak-1 2>&1 | grep -iE 'AuthenticationException|LDAP: error code|LOGIN_ERROR' | tail -3 | cut -c1-260"
run sh -c "docker logs --since 2m zerogate-openldap-1 2>&1 | grep -E 'BIND dn=\"cn=keycloak-svc|RESULT tag=97 err=49' | tail -4"
run dc exec -T openldap ldapwhoami -x -H ldap://127.0.0.1 -D "cn=keycloak-svc,ou=services,dc=zerogate,dc=lab" -w "$LDAP_KC_PW"
run dc exec -T openldap ldapwhoami -x -H ldap://127.0.0.1 -D "uid=dave,ou=people,dc=zerogate,dc=lab" -w "$LAB_PW"
