import pathlib
import subprocess
import sys

import pytest
import requests

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "testing/e2e"))
COMPOSE = ["docker", "compose", "-f", str(ROOT / "infrastructure/docker-compose.yml")]
ENV = dict(line.split("=", 1) for line in (ROOT / "infrastructure/.env").read_text().splitlines()
           if "=" in line and not line.startswith("#"))
PW = ENV["LAB_USER_PASSWORD"]
API = "http://localhost:8800/api"
KC_TOKEN = "http://localhost:8080/realms/zerogate/protocol/openid-connect/token"


def cexec(service: str, cmd: str, timeout: int = 40) -> subprocess.CompletedProcess:
    """Run a shell command inside a lab container."""
    return subprocess.run([*COMPOSE, "exec", "-T", service, "sh", "-c", cmd], capture_output=True, text=True, timeout=timeout)


def curl_code(service: str, args: str) -> str:
    """HTTP status as seen by curl in a client container ('000' if the transfer failed). Also returns the CONNECT status."""
    return cexec(service, f"curl -s -o /dev/null -w '%{{http_code}}/%{{http_connect}}' --max-time 20 {args}").stdout.strip()


def get_token(user: str) -> str:
    r = requests.post(KC_TOKEN, data={"grant_type": "password", "client_id": "zerogate-cli", "username": user, "password": PW}, timeout=15)
    r.raise_for_status()
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers():
    return {"Authorization": f"Bearer {get_token('alice')}"}


@pytest.fixture(scope="session")
def swg():
    return lambda user: f"-x 'http://{user}:{PW}@10.20.0.20:3128'"
