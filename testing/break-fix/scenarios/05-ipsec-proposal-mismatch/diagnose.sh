#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
run dc exec -T client-ipsec sh -c "swanctl --list-sas | head -3; echo '(no SA listed above = not connected)'"
run dc exec -T client-ipsec sh -c "swanctl --initiate --child corp --timeout 10 2>&1 | tail -6"
run sh -c "docker logs --since 1m zerogate-ipsec-gw-1 2>&1 | grep -E 'received proposals|configured proposals|no proposal|NO_PROP' | tail -4 | cut -c1-240"
run dc exec -T client-ipsec sh -c "grep -E 'proposals' /etc/swanctl/conf.d/client.conf"
run dc exec -T ipsec-gw sh -c "grep -E 'proposals' /etc/swanctl/conf.d/gateway.conf"
