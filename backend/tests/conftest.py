import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
os.environ.setdefault("AUTH_ENABLED", "false")
os.environ.setdefault("PKI_DIR", str(ROOT / "infrastructure/pki"))
os.environ.setdefault("TICKETS_DIR", str(ROOT / "tickets"))
os.environ.setdefault("SCENARIOS_DIR", str(ROOT / "testing/break-fix/scenarios"))
