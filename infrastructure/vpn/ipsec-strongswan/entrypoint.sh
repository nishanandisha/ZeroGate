#!/bin/bash
set -euo pipefail
S=/etc/swanctl
cp /pki/root-ca/root.crt /pki/intermediate-ca/issuing.crt $S/x509ca/
cp /pki/issued/ipsec-gw.crt $S/x509/
cp /pki/issued/ipsec-gw.key $S/private/ && chmod 600 $S/private/*

# NAT tunnel users toward corp/edge, same segmentation idea as the WireGuard gateway
iptables -t nat -F POSTROUTING
iptables -F FORWARD; iptables -P FORWARD DROP
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -s 10.98.0.0/24 -p icmp -j ACCEPT
iptables -A FORWARD -s 10.98.0.0/24 -d 10.10.0.40 -p tcp --dport 443  -j ACCEPT   # SAML app
iptables -A FORWARD -s 10.98.0.0/24 -d 10.20.0.20 -p tcp --dport 3128 -j ACCEPT   # Squid SWG
iptables -A FORWARD -s 10.98.0.0/24 -d 10.20.0.21 -p tcp --dport 8080 -j ACCEPT   # mitmproxy DLP
iptables -A FORWARD -s 10.98.0.0/24 -j REJECT --reject-with icmp-admin-prohibited
for net in 10.10.0.0/24 10.20.0.0/24; do iptables -t nat -A POSTROUTING -s 10.98.0.0/24 -d $net -j MASQUERADE; done

rm -f /var/run/charon.*
/usr/lib/strongswan/charon &
for i in $(seq 1 30); do swanctl --stats >/dev/null 2>&1 && break; sleep 0.5; done
swanctl --load-all
echo "[ipsec] gateway ready"
trap 'kill %1; exit 0' TERM INT
while true; do
  { echo "# ts=$(date +%s)"; swanctl --list-sas 2>&1; } > /status/ipsec.tmp && mv /status/ipsec.tmp /status/ipsec.txt
  sleep 5 & wait $!
done
