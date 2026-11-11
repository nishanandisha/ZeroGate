#!/bin/sh
# DLP lane: mitmdump with the ZeroGate inspection CA and the DLP/flow-log addon.
set -e
mkdir -p /conf /logs
if [ "${MITM_SEND_CHAIN:-true}" = "false" ]; then
  # Fault injection (TKT-007): CA file holds only key + Inspection CA, so the intermediate is not sent
  # and clients that trust only the Root cannot build a path.
  echo "[dlp] WARNING: fault injected - intermediate CA will not be sent in the TLS chain"
  cat /pki/intermediate-ca/inspection.key /pki/intermediate-ca/inspection.crt > /conf/mitmproxy-ca.pem
else
  # key + Inspection CA + Root: mitmproxy sends the extra certs in this file as the chain
  cat /pki/intermediate-ca/inspection.key /pki/intermediate-ca/inspection-chain.crt > /conf/mitmproxy-ca.pem
fi
cp /pki/intermediate-ca/inspection.crt /conf/mitmproxy-ca-cert.pem
exec mitmdump --mode regular --listen-port 8080 --set confdir=/conf --set block_global=false \
     --set flow_detail=0 -s /addons/zerogate_dlp.py
