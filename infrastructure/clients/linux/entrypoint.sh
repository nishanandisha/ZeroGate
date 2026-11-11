#!/bin/bash
# ZeroGate Linux endpoint: trusts the Root CA, connects the tunnel (MODE=wireguard|ipsec), points at the proxy.
set -uo pipefail
cp /pki/root-ca/root.crt /usr/local/share/ca-certificates/zerogate-root.crt && update-ca-certificates >/dev/null 2>&1
cat > /etc/profile.d/zerogate.sh <<P
export LAB_USER=${LAB_USER:-alice}
export ZG_PROXY=http://10.20.0.20:3128
export ZG_DLP_PROXY=http://10.20.0.21:8080
P
zg up || echo "[client] tunnel failed to come up - see 'zg status'"
trap 'zg down; exit 0' TERM INT
sleep infinity & wait $!
