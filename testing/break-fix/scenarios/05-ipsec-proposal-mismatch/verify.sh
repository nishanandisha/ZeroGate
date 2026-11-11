#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
dc exec -T client-ipsec sh -c 'swanctl --list-sas | grep -q ESTABLISHED && ping -c2 -W2 10.10.0.40 >/dev/null'
