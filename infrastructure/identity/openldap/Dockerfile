FROM alpine:3.20
RUN apk add --no-cache openldap openldap-back-mdb openldap-clients \
 && mkdir -p /run/openldap /var/lib/openldap/openldap-data
COPY slapd.conf.tmpl /etc/openldap/slapd.conf.tmpl
COPY ldif/ /seed/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 389
HEALTHCHECK --interval=10s --timeout=3s --retries=10 CMD ldapsearch -x -H ldap://127.0.0.1 -b "" -s base >/dev/null || exit 1
ENTRYPOINT ["/entrypoint.sh"]
