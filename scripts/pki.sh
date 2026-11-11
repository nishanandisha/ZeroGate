#!/bin/sh
# Build the lab PKI inside a throwaway alpine container.
cd "$(dirname "$0")/.."
docker run --rm -e FORCE="${FORCE:-0}" -v "$PWD/infrastructure/pki:/pki" -w /pki alpine:3.20 sh /pki/build-pki.sh
