#!/bin/bash
esc(){ sed 's/&/\&amp;/g;s/</\&lt;/g;s/>/\&gt;/g' <<<"$1"; }
printf 'Content-Type: text/html\r\n\r\n'
cat <<HTML
<!doctype html><html><head><meta charset="utf-8"><title>ZeroGate Private App</title>
<style>body{font-family:system-ui;max-width:720px;margin:40px auto;padding:0 16px;color:#0f172a}
.card{border:1px solid #cbd5e1;border-radius:12px;padding:20px}td{padding:4px 12px 4px 0}code{background:#f1f5f9;padding:2px 6px;border-radius:4px}</style></head>
<body><h1>🔒 ZeroGate Private App</h1><div class="card"><p>Authenticated via <b>SAML 2.0</b> (Keycloak → OpenLDAP).</p>
<table>
<tr><td>User (NameID)</td><td><code>$(esc "${MELLON_NAME_ID:-?}")</code></td></tr>
<tr><td>Email</td><td><code>$(esc "${MELLON_email:-}")</code></td></tr>
<tr><td>Groups</td><td><code>$(esc "${MELLON_groups:-}")</code></td></tr>
<tr><td>IdP</td><td><code>$(esc "${MELLON_IDP:-}")</code></td></tr>
<tr><td>Source IP</td><td><code>$(esc "$REMOTE_ADDR")</code></td></tr>
</table><p><a href="/admin">Admin area</a> (requires <code>zg-admins</code>) · <a href="/mellon/logout?ReturnTo=/healthz">Log out</a></p></div></body></html>
HTML
