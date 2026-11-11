#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
dc exec -T client-wg ping -c2 -W2 10.10.0.40 >/dev/null
