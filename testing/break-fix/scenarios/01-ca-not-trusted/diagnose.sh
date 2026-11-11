#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
P="http://alice:$LAB_PW@10.20.0.20:3128"
run dc exec -T client-wg sh -c "curl -sS -o /dev/null --max-time 15 -x $P https://example.com; echo exit=\$?"
run dc exec -T client-wg sh -c "curl -sv -o /dev/null --max-time 15 -x $P https://example.com 2>&1 | grep -E 'subject:|issuer:|SSL certificate problem'"
run dc exec -T client-wg sh -c "echo | openssl s_client -proxy 10.20.0.20:3128 -proxy_user alice -proxy_pass '$LAB_PW' -connect example.com:443 -servername example.com 2>/dev/null | grep -E '^ [0-9] s:|^   i:|Verify return code'"
run dc exec -T client-wg sh -c "grep -c 'ZeroGate' /etc/ssl/certs/ca-certificates.crt; ls /usr/local/share/ca-certificates/"
run dc exec -T client-wg sh -c "curl -s -o /dev/null -w 'with --cacert root.crt: HTTP %{http_code}\n' --cacert /pki/root-ca/root.crt --max-time 15 -x $P https://example.com"
