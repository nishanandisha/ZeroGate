FROM mitmproxy/mitmproxy:11.0.2
COPY addons/ /addons/
COPY entrypoint.sh /zg-entrypoint.sh
USER root
RUN chmod +x /zg-entrypoint.sh
EXPOSE 8080
ENTRYPOINT ["/zg-entrypoint.sh"]
