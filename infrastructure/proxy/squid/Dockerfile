FROM ubuntu:24.04
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends squid-openssl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
COPY squid.conf /etc/squid/squid.conf
COPY policy/ /etc/squid/policy/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 3128
# `squid -k check` signals the running process; it opens no connection, so it adds nothing to the access log
HEALTHCHECK --interval=15s CMD squid -k check 2>/dev/null || exit 1
ENTRYPOINT ["/entrypoint.sh"]
