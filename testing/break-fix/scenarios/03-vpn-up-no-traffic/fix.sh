#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
dc exec -T vpn-gw /usr/local/bin/policy.sh apply
