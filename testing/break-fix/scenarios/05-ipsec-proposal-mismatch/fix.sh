#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
dc exec -T client-ipsec zg down >/dev/null 2>&1
dc exec -T client-ipsec zg up >/dev/null 2>&1; sleep 2
