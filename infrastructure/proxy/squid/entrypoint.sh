#!/bin/bash
set -euo pipefail
install -d -o proxy -g proxy -m 750 /etc/squid/ssl /var/spool/squid
install -d -o proxy -g proxy -m 755 /var/log/squid
chmod -f 644 /var/log/squid/*.log || true
install -o proxy -g proxy -m 640 /pki/intermediate-ca/inspection-chain.crt /etc/squid/ssl/inspection.crt
install -o proxy -g proxy -m 600 /pki/intermediate-ca/inspection.key /etc/squid/ssl/inspection.key
printf '%s' "${LDAP_SQUID_PASSWORD:?}" > /etc/squid/ldap.pass && chown proxy:proxy /etc/squid/ldap.pass && chmod 600 /etc/squid/ldap.pass
if [ ! -d /var/lib/squid/ssl_db ]; then
  mkdir -p /var/lib/squid && /usr/lib/squid/security_file_certgen -c -s /var/lib/squid/ssl_db -M 8MB && chown -R proxy:proxy /var/lib/squid
fi
rm -f /run/squid.pid
squid -k parse >/dev/null 2>&1 || { squid -k parse; exit 1; }
exec squid -N -d 1
