#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
"$PY" "$ROOT/testing/e2e/saml_login.py" alice "$LAB_PW" / | head -1 | grep -q '^200 https://localhost:8443/$'
