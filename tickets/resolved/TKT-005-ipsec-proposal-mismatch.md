# TKT-005: IKEv2 VPN fails to connect immediately

| Field | Value |
|---|---|
| Severity | P3 |
| Component | VPN / IPsec |
| Environment | One client (strongSwan; same pattern as the Windows built-in client) |
| Status | Resolved |
| Scenario | 05-ipsec-proposal-mismatch |

## 1. Symptom (as reported)
"The IPsec VPN fails at once. No password prompt, no delay. WireGuard works from the same laptop."

## 2. Reproduction
`make break S=05` reconnects the client offering only `aes128-sha1-modp1024`.

## 3. Investigation
An instant failure means the gateway is reachable and answering. The client log shows the answer:
```
[NET] sending packet: from 172.30.0.101[500] to 172.30.0.11[500] (336 bytes)
[NET] received packet: from 172.30.0.11[500] to 172.30.0.101[500] (36 bytes)
[ENC] parsed IKE_SA_INIT response 0 [ N(NO_PROP) ]
[IKE] received NO_PROPOSAL_CHOSEN notify error
```
It fails in the first exchange (IKE_SA_INIT), before certificates or identities are involved. The gateway log puts the
two sides next to each other:
```
received proposals:   IKE:AES_CBC_128/HMAC_SHA1_96/PRF_HMAC_SHA1/MODP_1024
configured proposals: IKE:AES_GCM_16_256/PRF_HMAC_SHA2_384/ECP_384,
                      IKE:AES_CBC_256/HMAC_SHA2_256_128/PRF_HMAC_SHA2_256/MODP_2048,
                      IKE:AES_CBC_256/HMAC_SHA2_256_128/PRF_HMAC_SHA2_256/ECP_256
received proposals unacceptable
```

## 4. Root cause
The two ends share no IKE cipher suite. The client offered AES-128 / SHA-1 / DH group 2 (1024-bit), which the gateway
does not accept by policy. With nothing in common, the gateway replies `NO_PROPOSAL_CHOSEN`.

## 5. Fix
Change the **client** to a suite the gateway offers, not the other way round (`make fix S=05`):
```
proposals = aes256gcm16-prfsha384-ecp384
```
Windows equivalent: `Set-VpnConnectionIPsecConfiguration ... -EncryptionMethod AES256 -IntegrityCheckMethod SHA256 -DHGroup Group14`.

## 6. Verification
`swanctl --list-sas` shows `ESTABLISHED ... AES_GCM_16-256/PRF_HMAC_SHA2_384/ECP_384`; ping to `10.10.0.40` works.

## 7. Prevention / KB notes
* Where it fails tells you what it is: IKE_SA_INIT → proposals or reachability. IKE_AUTH → certificates, identities, or
  PSK. Tunnel up but no traffic → traffic selectors, routing, NAT (TKT-003).
* The gateway log is the better source: it prints both lists. The client only sees "no".
* A second `NO_PROPOSAL_CHOSEN` can appear later for the ESP (child SA) proposals. Same fix, different setting.
* Do not add SHA-1 or 1024-bit DH to the gateway to make one client work.
* Side finding while building this: a failed attempt left a half-open IKE SA that blocked the next connect until the
  daemon was restarted.
