#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
# Refresh the SP's copy of the IdP metadata (the entrypoint re-downloads it on start)
dc restart saml-app >/dev/null 2>&1; wait_healthy saml-app
