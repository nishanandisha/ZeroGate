FROM debian:bookworm-slim
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      apache2 libapache2-mod-auth-mellon faketime curl ca-certificates openssl xmlstarlet \
 && a2dismod -f mpm_event >/dev/null && a2enmod mpm_prefork ssl headers cgi auth_mellon >/dev/null && a2dissite 000-default >/dev/null \
 && rm -rf /var/lib/apt/lists/*
COPY zerogate-app.conf /etc/apache2/sites-available/zerogate-app.conf
COPY cgi/ /var/www/cgi/
COPY entrypoint.sh /entrypoint.sh
RUN a2ensite zerogate-app >/dev/null && chmod +x /entrypoint.sh /var/www/cgi/*.sh && mkdir -p /etc/apache2/mellon /etc/apache2/ssl
EXPOSE 443
HEALTHCHECK --interval=10s CMD curl -skf https://127.0.0.1/healthz >/dev/null || exit 1
ENTRYPOINT ["/entrypoint.sh"]
