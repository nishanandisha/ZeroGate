<#
.SYNOPSIS Installs WireGuard for Windows (if missing) and installs the ZeroGate tunnel as a service.
#>
param([Parameter(Mandatory)][string]$Profile, [string]$TunnelName = 'zerogate')
#Requires -RunAsAdministrator
$ErrorActionPreference = 'Stop'
$wg = "$env:ProgramFiles\WireGuard\wireguard.exe"
if (-not (Test-Path $wg)) {
  Write-Host "Installing WireGuard..."
  winget install --id WireGuard.WireGuard -e --accept-source-agreements --accept-package-agreements | Out-Null
}
$dest = "$env:ProgramFiles\WireGuard\Data\Configurations\$TunnelName.conf"
Copy-Item $Profile "$env:TEMP\$TunnelName.conf" -Force
& $wg /installtunnelservice "$env:TEMP\$TunnelName.conf"
Start-Sleep 3
& "$env:ProgramFiles\WireGuard\wg.exe" show $TunnelName
Get-Service "WireGuardTunnel`$$TunnelName" | Format-Table Name, Status
