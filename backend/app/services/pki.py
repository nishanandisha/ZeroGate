from datetime import datetime, timezone
from pathlib import Path

from cryptography import x509

from app.schemas.models import CertInfo


def _name(n: x509.Name) -> str:
    cn = n.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
    return cn[0].value if cn else n.rfc4514_string()


def describe(path: Path, warn_days: int, now: datetime | None = None) -> CertInfo:
    cert = x509.load_pem_x509_certificate(path.read_bytes())
    now = now or datetime.now(timezone.utc)
    days = (cert.not_valid_after_utc - now).days
    try:
        is_ca = cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
    except x509.ExtensionNotFound:
        is_ca = False
    try:
        san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        san = [str(v.value) for v in san_ext]
    except x509.ExtensionNotFound:
        san = []
    status = "down" if days < 0 or now < cert.not_valid_before_utc else "degraded" if days < warn_days else "up"
    return CertInfo(
        file=f"{path.parent.name}/{path.name}", subject=_name(cert.subject), issuer=_name(cert.issuer),
        serial=format(cert.serial_number, "x"), not_before=cert.not_valid_before_utc.isoformat(),
        not_after=cert.not_valid_after_utc.isoformat(), days_left=days, is_ca=is_ca, san=san, status=status,
    )


def inventory(pki_dir: str, warn_days: int) -> list[CertInfo]:
    root = Path(pki_dir)
    files = [p for p in sorted(root.glob("*/*.crt")) if "chain" not in p.name]
    return [describe(p, warn_days) for p in files]
