#!/bin/bash
# ZeroGate protected app: Apache + mod_auth_mellon (SAML SP) federated to Keycloak.
set -euo pipefail
M=/etc/apache2/mellon
install -m 644 /pki/issued/saml-app-fullchain.crt /etc/apache2/ssl/app-fullchain.crt
install -m 600 /pki/issued/saml-app.key           /etc/apache2/ssl/app.key
install -m 644 /pki/issued/saml-sp-sign.crt       $M/sp.crt
install -m 600 /pki/issued/saml-sp-sign.key       $M/sp.key
chown www-data $M/sp.key

# SP metadata
CERT=$(sed '/-----/d' $M/sp.crt | tr -d '\n')
cat > $M/sp-metadata.xml <<XML
<?xml version="1.0"?>
<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" entityID="${SP_BASE_URL}/mellon/metadata">
  <SPSSODescriptor AuthnRequestsSigned="true" WantAssertionsSigned="true" protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <KeyDescriptor use="signing"><ds:KeyInfo><ds:X509Data><ds:X509Certificate>${CERT}</ds:X509Certificate></ds:X509Data></ds:KeyInfo></KeyDescriptor>
    <SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" Location="${SP_BASE_URL}/mellon/logout"/>
    <NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified</NameIDFormat>
    <AssertionConsumerService index="0" isDefault="true" Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" Location="${SP_BASE_URL}/mellon/postResponse"/>
  </SPSSODescriptor>
</EntityDescriptor>
XML

# IdP metadata (retry until Keycloak has imported the realm)
for i in $(seq 1 60); do
  curl -sf "$IDP_METADATA_URL" -o $M/idp-metadata.xml.new && grep -q IDPSSODescriptor $M/idp-metadata.xml.new && break
  echo "[app] waiting for IdP metadata ($i)"; sleep 3
done
mv $M/idp-metadata.xml.new $M/idp-metadata.xml
echo "[app] IdP signing cert fingerprint: $(xmlstarlet sel -N ds=http://www.w3.org/2000/09/xmldsig# -t -v '(//ds:X509Certificate)[1]' $M/idp-metadata.xml | base64 -d | openssl x509 -inform der -noout -fingerprint -sha256 | cut -d= -f2)"

export SP_BASE_URL
if [ -n "${FAKETIME_OFFSET:-}" ]; then
  # Break/fix TKT-002: run Apache with a skewed clock
  export LD_PRELOAD=$(find /usr/lib -name libfaketime.so.1 | head -1) FAKETIME="$FAKETIME_OFFSET" FAKETIME_DONT_FAKE_MONOTONIC=1
  echo "[app] WARNING: clock skew injected ($FAKETIME_OFFSET) -> apache sees $(date)"
fi
rm -f /var/run/apache2/apache2.pid
set +u; source /etc/apache2/envvars; set -u
mkdir -p "$APACHE_RUN_DIR" "$APACHE_LOCK_DIR" "$APACHE_LOG_DIR"
exec apache2 -D FOREGROUND
