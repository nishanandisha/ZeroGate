#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
run dc exec -T client-wg sh -c "curl -sS -o /dev/null --max-time 15 -x http://10.20.0.21:8080 https://example.com; echo dlp-proxy exit=\$?"
run dc exec -T client-wg sh -c "curl -sS -o /dev/null --max-time 15 -x 'http://alice:$LAB_PW@10.20.0.20:3128' https://example.com; echo main-proxy exit=\$?"
run dc exec -T client-wg sh -c "grep -c 'ZeroGate Root CA' /etc/ssl/certs/ca-certificates.crt || openssl x509 -in /usr/local/share/ca-certificates/zerogate-root.crt -noout -subject"
run dc exec -T client-wg sh -c "echo 'chain sent by DLP proxy:'; echo | openssl s_client -proxy 10.20.0.21:8080 -connect example.com:443 -servername example.com -showcerts 2>/dev/null | grep -E '^ [0-9] s:|^   i:|Verify return code'"
run dc exec -T client-wg sh -c "echo 'chain sent by main proxy:'; echo | openssl s_client -proxy 10.20.0.20:3128 -proxy_user alice -proxy_pass '$LAB_PW' -connect example.com:443 -servername example.com -showcerts 2>/dev/null | grep -E '^ [0-9] s:|^   i:|Verify return code'"
