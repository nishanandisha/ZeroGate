<#
.SYNOPSIS Points both proxy stacks (WinINET for browsers, WinHTTP for services like Windows Update) at the SWG.
#>
param([string]$Proxy = '10.20.0.20:3128', [string]$Bypass = '<local>;10.10.0.*')
#Requires -RunAsAdministrator
$reg = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
Set-ItemProperty $reg ProxyEnable 1
Set-ItemProperty $reg ProxyServer $Proxy
Set-ItemProperty $reg ProxyOverride $Bypass
netsh winhttp set proxy proxy-server="$Proxy" bypass-list="$Bypass" | Out-Null
Write-Host "WinINET:"; Get-ItemProperty $reg | Select-Object ProxyEnable, ProxyServer, ProxyOverride | Format-List
Write-Host "WinHTTP:"; netsh winhttp show proxy
