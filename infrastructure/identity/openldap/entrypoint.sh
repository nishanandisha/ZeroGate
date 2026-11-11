#!/bin/sh
# Render slapd.conf with hashed secrets, seed the directory on first boot, run slapd in the foreground.
set -eu
h() { slappasswd -h '{SSHA}' -s "$1"; }
sed "s|__ROOT_PW__|$(h "${LDAP_ADMIN_PASSWORD:?}")|" /etc/openldap/slapd.conf.tmpl > /etc/openldap/slapd.conf
chmod 600 /etc/openldap/slapd.conf
DATA=/var/lib/openldap/openldap-data
if [ ! -f "$DATA/data.mdb" ]; then
  echo "[ldap] seeding directory"
  for f in /seed/*.ldif; do
    sed -e "s|__USER_PW__|$(h "${LAB_USER_PASSWORD:?}")|" \
        -e "s|__KEYCLOAK_SVC_PW__|$(h "${LDAP_KEYCLOAK_PASSWORD:?}")|" \
        -e "s|__SQUID_SVC_PW__|$(h "${LDAP_SQUID_PASSWORD:?}")|" \
        -e "s|__CONSOLE_SVC_PW__|$(h "${LDAP_CONSOLE_PASSWORD:?}")|" "$f" \
      | slapadd -f /etc/openldap/slapd.conf
  done
fi
# -d stats: every BIND/SRCH with result codes goes to docker logs (used in tickets)
exec slapd -d stats -h "ldap:///" -f /etc/openldap/slapd.conf
