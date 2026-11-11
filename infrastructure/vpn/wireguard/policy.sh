#!/bin/bash
# Zero-trust segmentation for tunnel users: default deny, allow only published services.
# usage: policy.sh apply|flush|show
set -eu
TUN=10.99.0.0/24
case "${1:-apply}" in
apply)
  iptables -F FORWARD; iptables -t nat -F POSTROUTING
  iptables -P FORWARD DROP
  iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  iptables -A FORWARD -i wg0 -p icmp -j ACCEPT
  iptables -A FORWARD -i wg0 -d 10.10.0.40 -p tcp --dport 443  -j ACCEPT   # SAML app
  iptables -A FORWARD -i wg0 -d 10.20.0.20 -p tcp --dport 3128 -j ACCEPT   # Squid SWG
  iptables -A FORWARD -i wg0 -d 10.20.0.21 -p tcp --dport 8080 -j ACCEPT   # mitmproxy DLP
  iptables -A FORWARD -i wg0 -j LOG --log-prefix "ZG-WG-DENY " --log-level 4
  iptables -A FORWARD -i wg0 -j REJECT --reject-with icmp-admin-prohibited
  iptables -t nat -A POSTROUTING -s $TUN ! -o wg0 -j MASQUERADE
  echo "[policy] applied";;
flush) iptables -F FORWARD; iptables -P FORWARD ACCEPT; iptables -t nat -F POSTROUTING; echo "[policy] flushed";;
show)  iptables -L FORWARD -n -v --line-numbers; iptables -t nat -L POSTROUTING -n -v;;
esac
