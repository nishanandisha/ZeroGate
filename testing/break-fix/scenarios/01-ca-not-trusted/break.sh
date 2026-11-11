#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
dc exec -T client-wg sh -c 'rm -f /usr/local/share/ca-certificates/zerogate-root.crt && update-ca-certificates --fresh >/dev/null 2>&1'
