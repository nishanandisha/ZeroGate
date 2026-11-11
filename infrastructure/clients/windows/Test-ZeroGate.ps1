<# .SYNOPSIS End-to-end checks from the Windows endpoint. #>
$cred = Get-Credential -Message "ZeroGate (LDAP) credentials for the proxy"
function Check($name, [scriptblock]$b) { try { $r = & $b; Write-Host ("[PASS] {0} {1}" -f $name, $r) -ForegroundColor Green } catch { Write-Host "[FAIL] $name : $($_.Exception.Message)" -ForegroundColor Red } }
Check "Root CA trusted"   { (Get-ChildItem Cert:\LocalMachine\Root | Where-Object Subject -match 'ZeroGate Root CA').Thumbprint }
Check "Tunnel: app 443"   { (Test-NetConnection 10.10.0.40 -Port 443 -WarningAction SilentlyContinue).TcpTestSucceeded }
Check "Policy: LDAP deny" { if ((Test-NetConnection 10.10.0.20 -Port 389 -WarningAction SilentlyContinue).TcpTestSucceeded) { throw "LDAP reachable - segmentation broken" } else { "blocked" } }
Check "Inspected HTTPS"   {
  $req = [System.Net.HttpWebRequest]::Create('https://example.com'); $req.Proxy = New-Object System.Net.WebProxy('http://10.20.0.20:3128')
  $req.Proxy.Credentials = $cred.GetNetworkCredential(); $resp = $req.GetResponse(); $resp.Close()
  $req.ServicePoint.Certificate.Issuer }
