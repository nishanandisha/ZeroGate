#!/bin/sh
printf 'Content-Type: application/json\r\n\r\n{"status":"ok","service":"saml-app","time":"%s"}\n' "$(date -u +%FT%TZ)"
