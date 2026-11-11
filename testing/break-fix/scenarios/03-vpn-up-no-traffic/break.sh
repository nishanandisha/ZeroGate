#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
dc exec -T vpn-gw iptables -t nat -F POSTROUTING
