#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
dc exec -T client-wg sh -c 'cp /pki/root-ca/root.crt /usr/local/share/ca-certificates/zerogate-root.crt && update-ca-certificates >/dev/null 2>&1'
