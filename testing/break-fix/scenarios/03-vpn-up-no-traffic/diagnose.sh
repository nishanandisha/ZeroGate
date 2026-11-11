#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
run dc exec -T client-wg sh -c "wg show wg0 | grep -E 'endpoint|latest handshake|transfer'"
run dc exec -T client-wg sh -c "ping -c2 -W2 10.10.0.40 | tail -2"
run dc exec -T client-wg ip route get 10.10.0.40
run dc exec -T vpn-gw sh -c "cat /proc/sys/net/ipv4/ip_forward; iptables -L FORWARD -n -v | head -5"
run sh -c "docker exec zerogate-client-wg-1 ping -c2 -W1 10.10.0.40 >/dev/null 2>&1 & docker exec zerogate-vpn-gw-1 timeout 4 tcpdump -ni any icmp -c 4 2>/dev/null"
run dc exec -T vpn-gw iptables -t nat -L POSTROUTING -n -v
