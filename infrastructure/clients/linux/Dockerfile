FROM alpine:3.20
RUN apk add --no-cache bash curl openssl ca-certificates bind-tools iputils iproute2 tcpdump \
    wireguard-tools strongswan iptables
COPY strongswan.conf /etc/strongswan.conf
COPY entrypoint.sh zg /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/zg
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
