#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
run sh -c "'$PY' '$ROOT/testing/e2e/saml_login.py' alice '$LAB_PW' / | head -1"
run sh -c "docker logs --tail 40 zerogate-saml-app-1 2>&1 | grep -iE 'auth_mellon' | tail -4"
FP='openssl x509 -inform der -noout -fingerprint -sha256'
run sh -c "echo 'IdP signing cert the app trusts (cached metadata):'; docker exec zerogate-saml-app-1 sh -c \"xmlstarlet sel -N ds=http://www.w3.org/2000/09/xmldsig# -t -m '//ds:X509Certificate' -v . -n /etc/apache2/mellon/idp-metadata.xml | while read c; do echo \\\$c | base64 -d | $FP; done\""
run sh -c "echo 'IdP signing cert(s) Keycloak publishes now:'; docker exec zerogate-saml-app-1 sh -c \"curl -s http://10.10.0.30:8080/realms/zerogate/protocol/saml/descriptor | xmlstarlet sel -N ds=http://www.w3.org/2000/09/xmldsig# -t -m '//ds:X509Certificate' -v . -n | while read c; do echo \\\$c | base64 -d | $FP; done\""
