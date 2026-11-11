#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
dc exec -T keycloak /opt/keycloak/bin/kcadm.sh config credentials --server http://localhost:8080 --realm master --user "$KC_ADMIN" --password "$KC_ADMIN_PW" >/dev/null 2>&1
dc exec -T keycloak /opt/keycloak/bin/kcadm.sh create components -r zerogate -s name=rsa-rotated-$(date +%s) -s providerId=rsa-generated -s providerType=org.keycloak.keys.KeyProvider \
  -s 'config.priority=["'$(date +%s)'"]' -s 'config.keySize=["2048"]' -s 'config.algorithm=["RS256"]' >/dev/null 2>&1
