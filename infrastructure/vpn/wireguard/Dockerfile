FROM alpine:3.20
RUN apk add --no-cache wireguard-tools iproute2 iptables tcpdump bash
COPY entrypoint.sh policy.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/*.sh
EXPOSE 51820/udp
HEALTHCHECK --interval=10s CMD wg show wg0 >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
