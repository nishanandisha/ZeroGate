FROM alpine:3.20
RUN apk add --no-cache strongswan iproute2 iptables tcpdump bash
COPY swanctl-gateway.conf /etc/swanctl/conf.d/gateway.conf
COPY strongswan.conf /etc/strongswan.conf
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
EXPOSE 500/udp 4500/udp
HEALTHCHECK --interval=10s CMD swanctl --stats >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
