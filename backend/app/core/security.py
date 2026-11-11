"""OIDC bearer-token validation against the Keycloak realm JWKS."""
from dataclasses import dataclass, field

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings

_bearer = HTTPBearer(auto_error=False)
_jwks_clients: dict[str, jwt.PyJWKClient] = {}


@dataclass
class Principal:
    username: str
    groups: list[str] = field(default_factory=list)
    email: str | None = None


def _jwks(settings: Settings) -> jwt.PyJWKClient:
    url = f"{settings.keycloak_internal_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/certs"
    if url not in _jwks_clients:
        _jwks_clients[url] = jwt.PyJWKClient(url, cache_keys=True, lifespan=300)
    return _jwks_clients[url]


def decode_token(token: str, settings: Settings, key=None) -> dict:
    signing_key = key if key is not None else _jwks(settings).get_signing_key_from_jwt(token).key
    return jwt.decode(
        token,
        signing_key,
        algorithms=["RS256", "ES256"],
        audience=settings.api_audience,
        issuer=settings.keycloak_issuer,
        leeway=30,  # tolerate small clock skew (see TKT-002 for what happens without it)
        options={"require": ["exp", "iat", "iss", "aud"]},
    )


def current_principal(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> Principal:
    if not settings.auth_enabled:
        return Principal(username="auth-disabled", groups=[settings.admin_group])
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token", {"WWW-Authenticate": "Bearer"})
    try:
        claims = decode_token(creds.credentials, settings)
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"invalid token: {exc}", {"WWW-Authenticate": "Bearer"})
    except Exception as exc:  # JWKS unreachable etc.
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"cannot validate token: {exc}")
    return Principal(claims.get("preferred_username", claims["sub"]), claims.get("groups", []), claims.get("email"))


def require_admin(p: Principal = Depends(current_principal), settings: Settings = Depends(get_settings)) -> Principal:
    if settings.admin_group not in p.groups:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"requires group {settings.admin_group}")
    return p
