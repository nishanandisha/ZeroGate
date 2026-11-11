<#
.SYNOPSIS Installs the ZeroGate Root CA into LocalMachine\Root so inspected (re-signed) TLS validates.
#>
param([Parameter(Mandatory)][string]$RootCa)
#Requires -RunAsAdministrator
$ErrorActionPreference = 'Stop'
$cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2 (Resolve-Path $RootCa)
if ($cert.Subject -notmatch 'ZeroGate Root CA') { throw "Unexpected subject: $($cert.Subject)" }
$existing = Get-ChildItem Cert:\LocalMachine\Root | Where-Object Thumbprint -eq $cert.Thumbprint
if ($existing) { Write-Host "Already trusted: $($cert.Thumbprint)"; return }
Import-Certificate -FilePath $RootCa -CertStoreLocation Cert:\LocalMachine\Root | Out-Null
Write-Host "Installed ZeroGate Root CA  thumbprint=$($cert.Thumbprint)  expires=$($cert.NotAfter)"
# Firefox uses its own store unless enterprise roots are enabled
$ff = "$env:ProgramFiles\Mozilla Firefox\distribution"
if (Test-Path "$env:ProgramFiles\Mozilla Firefox") {
  New-Item -ItemType Directory -Force $ff | Out-Null
  '{"policies":{"Certificates":{"ImportEnterpriseRoots":true}}}' | Set-Content "$ff\policies.json"
  Write-Host "Firefox: ImportEnterpriseRoots enabled"
}
