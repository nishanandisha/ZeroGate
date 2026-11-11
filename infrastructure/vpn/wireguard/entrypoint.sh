#!/bin/bash
# ZeroGate WireGuard gateway.
#  - first boot: generates server + client keys and configs under /config
#  - brings up wg0 (10.99.0.1/24), applies segmentation policy + NAT
#  - publishes `wg show dump` (key material redacted) to /status every 5s for the control plane
set -euo pipefail
C=/config; mkdir -p $C/clients; umask 077
PEERS=("linux:10.99.0.2" "windows:10.99.0.3" "macos:10.99.0.4")

[ -f $C/server_private.key ] || { wg genkey | tee $C/server_private.key | wg pubkey > $C/server_public.key; echo "[wg] server keys generated"; }
for p in "${PEERS[@]}"; do
  n=${p%%:*}; ip=${p##*:}
  if [ ! -f $C/clients/${n}_private.key ]; then
    wg genkey | tee $C/clients/${n}_private.key | wg pubkey > $C/clients/${n}_public.key
    wg genpsk > $C/clients/${n}.psk
    echo "[wg] keys generated for peer $n ($ip)"
  fi
  # Native `wg setconf` format (used by the Linux lab client)
  cat > $C/clients/$n.conf <<CONF
[Interface]
PrivateKey = $(cat $C/clients/${n}_private.key)

[Peer]
PublicKey = $(cat $C/server_public.key)
PresharedKey = $(cat $C/clients/$n.psk)
Endpoint = ${WG_PUBLIC_ENDPOINT:-172.30.0.10}:51820
AllowedIPs = 10.10.0.0/24, 10.20.0.0/24
PersistentKeepalive = 25
CONF
  # wg-quick / Windows / macOS app format
  cat > $C/clients/$n-wgquick.conf <<CONF
[Interface]
PrivateKey = $(cat $C/clients/${n}_private.key)
Address = $ip/32
MTU = 1380

[Peer]
PublicKey = $(cat $C/server_public.key)
PresharedKey = $(cat $C/clients/$n.psk)
Endpoint = ${WG_PUBLIC_ENDPOINT:-172.30.0.10}:51820
AllowedIPs = 10.10.0.0/24, 10.20.0.0/24
PersistentKeepalive = 25
CONF
done
chmod 644 $C/clients/*.conf   # lab client container mounts these read-only

# Server config (wg setconf format)
{
  echo "[Interface]"; echo "PrivateKey = $(cat $C/server_private.key)"; echo "ListenPort = 51820"
  for p in "${PEERS[@]}"; do
    n=${p%%:*}; ip=${p##*:}
    printf '\n# %s\n[Peer]\nPublicKey = %s\nPresharedKey = %s\nAllowedIPs = %s/32\n' "$n" "$(cat $C/clients/${n}_public.key)" "$(cat $C/clients/$n.psk)" "$ip"
  done
} > $C/wg0.conf

ip link del wg0 2>/dev/null || true
ip link add wg0 type wireguard
wg setconf wg0 $C/wg0.conf
ip addr add 10.99.0.1/24 dev wg0
ip link set wg0 mtu 1420 up
/usr/local/bin/policy.sh apply
echo "[wg] gateway up: $(wg show wg0 listen-port) peers=$(wg show wg0 peers | wc -l)"

trap 'exit 0' TERM INT
while true; do
  { echo "# ts=$(date +%s) ip_forward=$(cat /proc/sys/net/ipv4/ip_forward)"; wg show wg0 dump | awk 'BEGIN{FS=OFS="\t"} NR==1{$1="(hidden)"} NR>1{$2="(hidden)"} {print}'; } > /status/wireguard.tmp && chmod 644 /status/wireguard.tmp && mv /status/wireguard.tmp /status/wireguard.txt
  sleep 5 & wait $!
done
