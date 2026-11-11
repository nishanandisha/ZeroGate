from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

client = TestClient(app)


def test_live_and_auth_config():
    assert client.get("/api/health/live").json() == {"status": "ok"}
    cfg = client.get("/api/auth/config").json()
    assert cfg["client_id"] == "zerogate-console"


def test_pki_inventory_from_repo():
    certs = client.get("/api/pki/certificates").json()
    names = {c["subject"] for c in certs}
    assert {"ZeroGate Root CA", "ZeroGate Inspection CA", "app.zerogate.lab"} <= names
    root = next(c for c in certs if c["subject"] == "ZeroGate Root CA")
    assert root["is_ca"] and root["status"] == "up"


def test_ticket_path_traversal_rejected():
    assert client.get("/api/tickets/..%2F..%2Fetc%2Fpasswd").status_code == 404


def test_auth_required_when_enabled(monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    get_settings.cache_clear()
    try:
        r = client.get("/api/me")
        assert r.status_code == 401
        r = client.get("/api/me", headers={"Authorization": "Bearer not-a-jwt"})
        assert r.status_code in (401, 503)
    finally:
        monkeypatch.delenv("AUTH_ENABLED")
        get_settings.cache_clear()
