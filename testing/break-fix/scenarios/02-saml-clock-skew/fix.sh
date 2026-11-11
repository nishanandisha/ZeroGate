#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
SAML_APP_FAKETIME_OFFSET= dc up -d saml-app >/dev/null 2>&1; wait_healthy saml-app
