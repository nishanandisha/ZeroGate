from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "ZeroGate Control Plane"
    auth_enabled: bool = True
    admin_group: str = "zg-admins"
    keycloak_internal_url: str = "http://10.10.0.30:8080"
    keycloak_issuer: str = "http://localhost:8080/realms/zerogate"
    keycloak_realm: str = "zerogate"
    oidc_client_id: str = "zerogate-console"
    api_audience: str = "zerogate-api"

    ldap_url: str = "ldap://10.10.0.20:389"
    ldap_bind_dn: str = "cn=console-svc,ou=services,dc=zerogate,dc=lab"
    ldap_bind_password: str = ""
    ldap_base: str = "dc=zerogate,dc=lab"

    pki_dir: str = "/pki"
    tickets_dir: str = "/data/tickets"
    scenarios_dir: str = "/data/scenarios"
    squid_log: str = "/logs/squid/access.log"
    mitm_log: str = "/logs/mitm/flows.jsonl"
    status_dir: str = "/status"

    saml_app_url: str = "https://10.10.0.40/healthz"
    squid_addr: str = "10.20.0.20:3128"
    mitm_addr: str = "10.20.0.21:8080"
    cert_warn_days: int = 30
    wg_handshake_stale_s: int = 180
    status_stale_s: int = 30
    cors_origins: list[str] = ["http://localhost:3300", "http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
