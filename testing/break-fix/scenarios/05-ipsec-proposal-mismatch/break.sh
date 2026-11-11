#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
dc exec -T client-ipsec zg down >/dev/null 2>&1
dc exec -T -e IKE_PROPOSALS=aes128-sha1-modp1024 client-ipsec zg up >/dev/null 2>&1; true
