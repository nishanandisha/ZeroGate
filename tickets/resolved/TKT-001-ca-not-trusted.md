# TKT-001: HTTPS sites show certificate errors behind the proxy

| Field | Value |
|---|---|
| Severity | P2 |
| Component | Proxy / Client |
| Environment | Linux client (same on Windows) |
| Status | Resolved |
| Scenario | 01-ca-not-trusted |

## 1. Symptom (as reported)
"Since I was moved onto the secure web gateway, every HTTPS site gives a certificate warning. HTTP sites work."

## 2. Reproduction
`make break S=01` removes the ZeroGate Root CA from the client's trust store.

## 3. Investigation
The request reaches the proxy and the proxy answers, so this is a trust problem and not a connectivity problem:
```
$ curl -x http://alice:***@10.20.0.20:3128 https://example.com
curl: (60) SSL certificate problem: self-signed certificate in certificate chain
```
Who issued the certificate the client is being shown? Not the real site. The proxy re-signed it:
```
issuer: C=US; O=ZeroGate Lab; OU=Security; CN=ZeroGate Inspection CA
```
Does the client trust our CA? Count of ZeroGate certificates in the system bundle:
```
$ grep -c ZeroGate /etc/ssl/certs/ca-certificates.crt
0
```
Confirm the theory by giving curl the root explicitly. Same proxy, same site:
```
with --cacert root.crt: HTTP 200
```

## 4. Root cause
The proxy performs SSL inspection: it ends the TLS session, then presents a certificate for the site signed by the
**ZeroGate Inspection CA**, which chains to the **ZeroGate Root CA**. This endpoint did not have the Root CA in its trust
store, so the chain ends in a root it has never seen. The wording "self-signed certificate in certificate chain" is the
clue: the chain is complete, but its root is unknown to the client.

## 5. Fix
```
cp root.crt /usr/local/share/ca-certificates/zerogate-root.crt && update-ca-certificates   # Linux
Import-Certificate -FilePath root.crt -CertStoreLocation Cert:\LocalMachine\Root         # Windows
```
(`make fix S=01`)

## 6. Verification
`curl` through the proxy returns 200 with no `--cacert`; issuer is still the Inspection CA.

## 7. Prevention / KB notes
* Push the root with device management (GPO / MDM) before a user is moved onto inspection, not after.
* Apps with their own trust store ignore the OS store: Firefox (enable enterprise roots), Java (`cacerts`), Python
  `requests` (`REQUESTS_CA_BUNDLE`), Node (`NODE_EXTRA_CA_CERTS`), Git. "Browser works, CLI tool fails" is this ticket again.
* Never tell users to click through the warning or use `curl -k`.
