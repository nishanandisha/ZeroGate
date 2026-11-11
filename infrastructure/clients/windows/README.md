# Windows client (VirtualBox)

The Windows endpoint is a real VM. It reaches the lab through ports that Docker publishes on the Mac.

## 1. VM
| Item | Value |
|---|---|
| Hypervisor | VirtualBox 7.1+ (Apple Silicon: Windows 11 ARM; Intel: Windows 10/11 x64), or UTM |
| NIC 1 | NAT (internet) |
| NIC 2 | Host-only network (e.g. `192.168.56.0/24`). The Mac is `192.168.56.1` |
| RAM / disk | 4 GB / 64 GB |

Set `WG_PUBLIC_ENDPOINT=192.168.56.1` in `infrastructure/.env`, then `make up`. The `windows-wgquick.conf` profile
then points at the Mac, and Docker forwards UDP 51820 to `vpn-gw`.

## 2. Copy files to the VM
From the repo: `infrastructure/pki/root-ca/root.crt`, `infrastructure/vpn/wireguard/config/clients/windows-wgquick.conf`,
`infrastructure/pki/issued/ipsec-alice.{crt,key}` + `intermediate-ca/issuing.crt`, and this folder's `*.ps1`.

## 3. Run (elevated PowerShell)
```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\Install-ZeroGateTrust.ps1  -RootCa .\root.crt            # TKT-001 lives or dies here
.\Connect-ZeroGateWireGuard.ps1 -Profile .\windows-wgquick.conf
.\Set-ZeroGateProxy.ps1 -Proxy 10.20.0.20:3128             # WinINET + WinHTTP
.\Test-ZeroGate.ps1
# Optional: native IKEv2 instead of WireGuard
.\Connect-ZeroGateIKEv2.ps1 -Gateway 192.168.56.1 -UserPfx .\alice.pfx
```
Make the PFX on the Mac with:
`openssl pkcs12 -export -in issued/ipsec-alice.crt -inkey issued/ipsec-alice.key -certfile intermediate-ca/issuing.crt -out alice.pfx`

## 4. What to show in an interview
* `certlm.msc` → Trusted Root → *ZeroGate Root CA*; Edge → padlock → issuer **ZeroGate Inspection CA**
* `Get-VpnConnection`, `Get-NetIPsecMainModeSA`, `wg show` for the tunnel state
* `netsh winhttp show proxy` vs Internet Options: the classic "browser works, Windows Update doesn't" proxy split
