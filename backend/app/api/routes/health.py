import asyncio

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.core.security import require_admin
from app.probes import files, network
from app.probes.base import timed
from app.schemas.models import ComponentHealth

router = APIRouter(prefix="/api/health", tags=["health"])

COMPONENTS = [
    ("openldap", "OpenLDAP directory", "identity", network.ldap),
    ("keycloak", "Keycloak IdP (SAML/OIDC)", "identity", network.keycloak),
    ("saml-app", "Private app (SAML SP)", "apps", network.saml_app),
    ("wireguard", "WireGuard gateway", "connect", files.wireguard),
    ("ipsec", "IPsec IKEv2 gateway", "connect", files.ipsec),
    ("squid", "Secure Web Gateway (Squid)", "inspect", network.squid),
    ("mitmproxy", "DLP proxy (mitmproxy)", "inspect", network.mitmproxy),
    ("pki", "PKI / certificates", "trust", files.pki_inventory),
]


@router.get("/live")
def live() -> dict:
    return {"status": "ok"}


@router.get("/components", response_model=list[ComponentHealth], dependencies=[Depends(require_admin)])
async def components(settings: Settings = Depends(get_settings)) -> list[ComponentHealth]:
    tasks = [asyncio.to_thread(timed, cid, name, cat, lambda f=fn: f(settings)) for cid, name, cat, fn in COMPONENTS]
    return list(await asyncio.gather(*tasks))
