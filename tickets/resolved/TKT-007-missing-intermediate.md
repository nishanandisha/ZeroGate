# TKT-007: Certificate errors only on the DLP proxy, although the Root CA is installed

| Field | Value |
|---|---|
| Severity | P2 |
| Component | Proxy / PKI |
| Environment | DLP proxy (mitmproxy) |
| Status | Resolved |
| Scenario | 07-missing-intermediate |

## 1. Symptom (as reported)
"We installed the Root CA as instructed (TKT-001). The main proxy is fine, but anything sent through the DLP proxy
still gets certificate errors."

## 2. Reproduction
`make break S=07` starts the DLP proxy with a CA file that lacks the chain.

## 3. Investigation
Same client, same site, two proxies:
```
dlp-proxy:  curl: (60) SSL certificate problem: unable to get local issuer certificate
main-proxy: exit=0
```
The root is present on the client, so this is not TKT-001:
```
subject=C=US, O=ZeroGate Lab, OU=Security, CN=ZeroGate Root CA
```
Note the error text differs from TKT-001 ("self-signed certificate in certificate chain"). Look at the chain the DLP
proxy actually sends:
```
 0 s:CN=example.com
   i:C=US, O=ZeroGate Lab, OU=Security, CN=ZeroGate Inspection CA
Verify return code: 21 (unable to verify the first certificate)
```
One certificate. Its issuer, the Inspection CA, is not sent, and the client does not have it.

## 4. Root cause
The PKI has three levels: Root → Inspection CA → per-site certificate. Clients trust only the Root. The server must
therefore send the intermediate (Inspection CA) with each certificate. The DLP proxy's CA file held only the key and
the Inspection CA certificate, so it sent the leaf alone and clients could not link it to the Root.
This happened for real while building the lab, before it became a scenario.

## 5. Fix
Put the chain in the proxy's CA file (key + Inspection CA + Root) so it is sent in the handshake (`make fix S=07`).

## 6. Verification
`curl` through the DLP proxy returns 200; `openssl s_client -showcerts` lists the Inspection CA after the leaf.

## 7. Prevention / KB notes
* Two different errors, two different faults: "self-signed certificate in certificate chain" → root not trusted
  (client side). "unable to get local issuer certificate" / code 21 → intermediate missing (server side).
* Do not fix this by installing the intermediate on every client. It works until the intermediate is rotated.
* Browsers can hide this fault by caching intermediates seen elsewhere; command-line tools do not. Test with `openssl s_client`.
