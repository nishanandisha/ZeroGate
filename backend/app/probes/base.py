import time
from collections.abc import Callable

from app.schemas.models import ComponentHealth


def timed(id_: str, name: str, category: str, fn: Callable[[], tuple[str, str, dict]]) -> ComponentHealth:
    """Run a probe function returning (status, detail, data); never raises."""
    start = time.perf_counter()
    try:
        status, detail, data = fn()
    except Exception as exc:  # a probe failure is a "down" result, not an API error
        status, detail, data = "down", f"{type(exc).__name__}: {exc}", {}
    return ComponentHealth(
        id=id_, name=name, category=category, status=status, detail=detail, data=data,
        latency_ms=round((time.perf_counter() - start) * 1000, 1), checked_at=time.time(),
    )
