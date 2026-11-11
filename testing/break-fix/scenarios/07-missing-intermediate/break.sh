#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
MITM_SEND_CHAIN=false dc up -d mitmproxy >/dev/null 2>&1
for i in $(seq 1 30); do dc exec -T client-wg nc -z -w 2 10.20.0.21 8080 2>/dev/null && break; sleep 1; done; sleep 2
