<#
.SYNOPSIS Native Windows IKEv2 (machine-certificate) VPN to the strongSwan gateway, with crypto that matches the gateway's proposals.
#>
param([Parameter(Mandatory)][string]$Gateway, [Parameter(Mandatory)][string]$UserPfx, [string]$Name = 'ZeroGate-IKEv2')
#Requires -RunAsAdministrator
$ErrorActionPreference = 'Stop'
$pw = Read-Host -AsSecureString "PFX password"
Import-PfxCertificate -FilePath $UserPfx -CertStoreLocation Cert:\LocalMachine\My -Password $pw | Out-Null
Remove-VpnConnection -Name $Name -AllUserConnection -Force -ErrorAction SilentlyContinue
Add-VpnConnection -Name $Name -ServerAddress $Gateway -TunnelType Ikev2 -AuthenticationMethod MachineCertificate `
  -EncryptionLevel Required -SplitTunneling -AllUserConnection -RememberCredential
# Windows' default IKE proposals are weak (3DES/SHA1/DH2); pin to what the gateway offers (aes256-sha256-modp2048)
Set-VpnConnectionIPsecConfiguration -ConnectionName $Name -AuthenticationTransformConstants SHA256128 `
  -CipherTransformConstants AES256 -EncryptionMethod AES256 -IntegrityCheckMethod SHA256 -DHGroup Group14 `
  -PfsGroup PFS2048 -AllUserConnection -Force
'10.10.0.0/24','10.20.0.0/24' | ForEach-Object { Add-VpnConnectionRoute -ConnectionName $Name -DestinationPrefix $_ -AllUserConnection }
# The gateway certificate's SAN is vpn.zerogate.lab; map it if you connect by name
rasdial $Name
Get-VpnConnection -Name $Name -AllUserConnection | Format-List Name, ConnectionStatus, ServerAddress
