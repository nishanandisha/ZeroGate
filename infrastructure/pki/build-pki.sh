#!/bin/sh
# ZeroGate PKI builder: Root CA -> {Issuing CA, Inspection CA} -> leaf certs.
# Runs inside an alpine container (see scripts/pki.sh) so OpenSSL behaves the same everywhere.
# Idempotent: existing keys are kept unless FORCE=1.
set -eu
cd "$(dirname "$0")"
command -v openssl >/dev/null || apk add --no-cache openssl >/dev/null

DOMAIN=${LAB_DOMAIN:-zerogate.lab}
SUBJ_BASE="/C=US/O=ZeroGate Lab"

if [ -f root-ca/root.crt ] && [ "${FORCE:-0}" != "1" ]; then
  echo "[pki] root CA exists - skipping CA creation (FORCE=1 to rebuild)"
else
  rm -rf root-ca/* intermediate-ca/* issued/*
  echo "[pki] creating Root CA"
  openssl genrsa -out root-ca/root.key 4096 2>/dev/null
  openssl req -x509 -new -key root-ca/root.key -sha256 -days 3650 \
    -subj "$SUBJ_BASE/OU=Security/CN=ZeroGate Root CA" \
    -addext "basicConstraints=critical,CA:TRUE" \
    -addext "keyUsage=critical,keyCertSign,cRLSign" \
    -addext "subjectKeyIdentifier=hash" \
    -out root-ca/root.crt

  for ca in issuing inspection; do
    case $ca in issuing) cn="ZeroGate Issuing CA"; days=1825;; inspection) cn="ZeroGate Inspection CA"; days=1095;; esac
    echo "[pki] creating $cn"
    openssl genrsa -out intermediate-ca/$ca.key 4096 2>/dev/null
    openssl req -new -key intermediate-ca/$ca.key -subj "$SUBJ_BASE/OU=Security/CN=$cn" -out intermediate-ca/$ca.csr
    cat > intermediate-ca/$ca.ext <<EOF
basicConstraints=critical,CA:TRUE,pathlen:0
keyUsage=critical,keyCertSign,cRLSign,digitalSignature
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always
EOF
    openssl x509 -req -in intermediate-ca/$ca.csr -CA root-ca/root.crt -CAkey root-ca/root.key \
      -CAcreateserial -days $days -sha256 -extfile intermediate-ca/$ca.ext -out intermediate-ca/$ca.crt 2>/dev/null
    cat intermediate-ca/$ca.crt root-ca/root.crt > intermediate-ca/$ca-chain.crt
  done
fi

# leaf <name> <CN> <SAN> <EKU>
leaf() {
  name=$1; cn=$2; san=$3; eku=$4
  [ -f issued/$name.crt ] && [ "${FORCE:-0}" != "1" ] && { echo "[pki] issued/$name.crt exists"; return; }
  echo "[pki] issuing $name ($cn)"
  openssl genrsa -out issued/$name.key 2048 2>/dev/null
  openssl req -new -key issued/$name.key -subj "$SUBJ_BASE/CN=$cn" -out issued/$name.csr
  cat > issued/$name.ext <<EOF
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=$eku
subjectAltName=$san
authorityKeyIdentifier=keyid
subjectKeyIdentifier=hash
EOF
  openssl x509 -req -in issued/$name.csr -CA intermediate-ca/issuing.crt -CAkey intermediate-ca/issuing.key \
    -CAcreateserial -days 825 -sha256 -extfile issued/$name.ext -out issued/$name.crt 2>/dev/null
  cat issued/$name.crt intermediate-ca/issuing.crt > issued/$name-fullchain.crt
  rm -f issued/$name.csr issued/$name.ext
}

leaf saml-app      "app.$DOMAIN"      "DNS:app.$DOMAIN,DNS:localhost,IP:10.10.0.40,IP:127.0.0.1" "serverAuth"
leaf saml-sp-sign  "saml-sp.$DOMAIN"  "DNS:saml-sp.$DOMAIN"                                      "serverAuth"
leaf console       "console.$DOMAIN"  "DNS:console.$DOMAIN,DNS:localhost,IP:127.0.0.1"           "serverAuth"
# IKEv2 gateway: serverAuth + ikeIntermediate (1.3.6.1.5.5.8.2.2) is what Windows wants
leaf ipsec-gw      "vpn.$DOMAIN"      "DNS:vpn.$DOMAIN,IP:172.30.0.11"                           "serverAuth,1.3.6.1.5.5.8.2.2"
for u in alice bob carol; do
  leaf ipsec-$u    "$u@$DOMAIN"       "email:$u@$DOMAIN"                                         "clientAuth"
done

# Engine-specific bundles for the inspection CA
cat intermediate-ca/inspection.key intermediate-ca/inspection.crt > intermediate-ca/mitmproxy-ca.pem
chmod 644 issued/*.key intermediate-ca/*.key intermediate-ca/mitmproxy-ca.pem root-ca/root.key  # lab only: containers run as non-root

echo "[pki] verify chains"
openssl verify -CAfile root-ca/root.crt -untrusted intermediate-ca/issuing.crt issued/saml-app.crt
openssl verify -CAfile root-ca/root.crt intermediate-ca/inspection.crt
echo "[pki] done"
