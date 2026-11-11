# Shared helpers for break/fix scenarios. Source me.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
dc() { docker compose -f "$ROOT/infrastructure/docker-compose.yml" "$@"; }
PY="$ROOT/testing/.venv/bin/python"
LAB_PW="$(grep ^LAB_USER_PASSWORD= "$ROOT/infrastructure/.env" | cut -d= -f2-)"
KC_ADMIN="$(grep ^KEYCLOAK_ADMIN= "$ROOT/infrastructure/.env" | cut -d= -f2-)"
KC_ADMIN_PW="$(grep ^KEYCLOAK_ADMIN_PASSWORD= "$ROOT/infrastructure/.env" | cut -d= -f2-)"
LDAP_ADMIN_PW="$(grep ^LDAP_ADMIN_PASSWORD= "$ROOT/infrastructure/.env" | cut -d= -f2-)"
LDAP_KC_PW="$(grep ^LDAP_KEYCLOAK_PASSWORD= "$ROOT/infrastructure/.env" | cut -d= -f2-)"
run() { echo "\$ $*"; "$@" 2>&1; echo; }          # echo a command, then run it (used by diagnose.sh)
wait_healthy() {                                   # wait_healthy <service> [seconds]
  local i; for i in $(seq 1 "${2:-60}"); do
    [ "$(docker inspect -f '{{.State.Health.Status}}' "zerogate-$1-1" 2>/dev/null)" = healthy ] && return 0; sleep 2
  done; echo "timeout waiting for $1"; return 1
}
token() { curl -s --max-time 10 -d grant_type=password -d client_id=zerogate-cli -d "username=$1" --data-urlencode "password=$LAB_PW" \
            http://localhost:8080/realms/zerogate/protocol/openid-connect/token; }
# Strip secrets and machine-specific paths from anything written to testing/reports (evidence is committed).
redact() {
  local secret; local -a args=()
  for secret in "$LAB_PW" "$KC_ADMIN_PW" "$LDAP_ADMIN_PW" "$LDAP_KC_PW"; do
    [ -n "$secret" ] && args+=(-e "s|$(printf '%s' "$secret" | sed 's/[][\\.*^$|/&]/\\&/g')|<redacted>|g")
  done
  sed "${args[@]}" -e "s|$ROOT|<repo>|g" -e "s|$HOME|~|g"
}
