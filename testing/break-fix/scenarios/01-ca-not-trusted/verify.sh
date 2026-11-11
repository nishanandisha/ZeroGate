#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
dc exec -T client-wg curl -sS -o /dev/null --max-time 15 -x "http://alice:$LAB_PW@10.20.0.20:3128" https://example.com
