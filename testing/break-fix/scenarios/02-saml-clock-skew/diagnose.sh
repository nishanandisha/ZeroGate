#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
run sh -c "'$PY' '$ROOT/testing/e2e/saml_login.py' alice '$LAB_PW' / | head -1"
run sh -c "docker logs --tail 40 zerogate-saml-app-1 2>&1 | grep -iE 'auth_mellon|skew' | tail -6"
run sh -c "docker logs --since 2m zerogate-keycloak-1 2>&1 | grep -E 'type=\"LOGIN' | tail -2 | cut -c1-230"
run sh -c "echo host:      \$(date -u +%FT%TZ); echo keycloak:  \$(docker exec zerogate-keycloak-1 date -u +%FT%TZ); echo saml-app:  \$(docker exec zerogate-saml-app-1 sh -c 'LD_PRELOAD=\$(find /usr/lib -name libfaketime.so.1 | head -1) FAKETIME=\${FAKETIME_OFFSET:-+0} date -u +%FT%TZ')"
run sh -c "docker exec zerogate-saml-app-1 env | grep FAKETIME"
