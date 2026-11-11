# TKT-003: VPN shows connected but nothing loads

| Field | Value |
|---|---|
| Severity | P1 |
| Component | VPN / WireGuard |
| Environment | All WireGuard users |
| Status | Resolved |
| Scenario | 03-vpn-up-no-traffic |

## 1. Symptom (as reported)
"The VPN connects, the icon is green, but the internal app and the proxy time out."

## 2. Reproduction
`make break S=03` flushes the NAT table on the gateway.

## 3. Investigation
Tunnel state on the client: handshake is recent and bytes flow both ways, so keys, endpoint and UDP reachability are fine.
```
endpoint: 172.30.0.10:51820
latest handshake: 1 minute, 35 seconds ago
transfer: 122.63 KiB received, 36.79 KiB sent
```
But traffic to the corporate network is lost, and the client is routing it into the tunnel correctly:
```
2 packets transmitted, 0 received, 100% packet loss
10.10.0.40 dev wg0 src 10.99.0.2
```
Move to the gateway. Forwarding is on and the firewall allows it:
```
ip_forward = 1
ACCEPT  icmp  --  wg0  *  0.0.0.0/0  0.0.0.0/0      (6 packets counted)
```
Packet capture on the gateway shows the request leaving toward the app **with the tunnel address as source**, and no reply:
```
wg0   In  IP 10.99.0.2 > 10.10.0.40: ICMP echo request
eth0  Out IP 10.99.0.2 > 10.10.0.40: ICMP echo request
```
The NAT table explains it. It is empty:
```
Chain POSTROUTING (policy ACCEPT)
 pkts bytes target  prot opt in  out  source  destination
```

## 4. Root cause
The gateway's `MASQUERADE` rule for `10.99.0.0/24` was gone. Requests arrived at the app with source `10.99.0.2`.
The app has no route to the tunnel network, so it sent the reply to its default gateway, where it was dropped.
One direction worked, the return path did not.

## 5. Fix
`policy.sh apply` on the gateway restores the rule (`make fix S=03`):
```
iptables -t nat -A POSTROUTING -s 10.99.0.0/24 ! -o wg0 -j MASQUERADE
```

## 6. Verification
Ping and HTTPS to `10.10.0.40` succeed from the client; the MASQUERADE packet counter increases.

## 7. Prevention / KB notes
"Tunnel up, no traffic" checklist, in order: (1) handshake recent? (2) client route and AllowedIPs, (3) gateway
`ip_forward`, (4) gateway firewall FORWARD, (5) **return path**: NAT or a route back on the far side, (6) MTU.
* Capture on both gateway interfaces. Seeing the request leave with no reply points at the return path straight away.
* Firewall rules applied by hand are lost on restart or by a flush. Keep them in a script that runs at boot.
* The control plane's WireGuard probe catches `ip_forward=0` but not a missing NAT rule. A synthetic ping through
  the tunnel would catch both (not built yet).
