#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
dc exec -T client-wg curl -sS -o /dev/null --max-time 15 -x http://10.20.0.21:8080 https://example.com
