from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.config import Settings, get_settings
from app.core.security import Principal, current_principal, require_admin
from app.schemas.models import CertInfo, Group, Scenario, Ticket, TicketSummary, TrafficEvent, User
from app.services import content, directory, pki, traffic

router = APIRouter(prefix="/api", dependencies=[Depends(require_admin)])


@router.get("/me", tags=["auth"])
def me(p: Principal = Depends(current_principal)) -> dict:
    return {"username": p.username, "groups": p.groups, "email": p.email}


@router.get("/directory/users", response_model=list[User], tags=["directory"])
def list_users(s: Settings = Depends(get_settings)):
    try:
        return directory.users(s)
    except ConnectionError as exc:
        raise HTTPException(502, str(exc))


@router.get("/directory/groups", response_model=list[Group], tags=["directory"])
def list_groups(s: Settings = Depends(get_settings)):
    try:
        return directory.groups(s)
    except ConnectionError as exc:
        raise HTTPException(502, str(exc))


@router.get("/traffic/events", response_model=list[TrafficEvent], tags=["traffic"])
def traffic_events(limit: int = Query(200, ge=1, le=2000), user: str | None = None, action: str | None = None,
                   s: Settings = Depends(get_settings)):
    ev = traffic.events(s.squid_log, s.mitm_log, limit)
    return [e for e in ev if (not user or e.user == user) and (not action or e.action == action)]


@router.get("/traffic/stats", tags=["traffic"])
def traffic_stats(limit: int = Query(1000, ge=1, le=5000), s: Settings = Depends(get_settings)):
    return traffic.stats(traffic.events(s.squid_log, s.mitm_log, limit))


@router.get("/pki/certificates", response_model=list[CertInfo], tags=["pki"])
def certificates(s: Settings = Depends(get_settings)):
    return pki.inventory(s.pki_dir, s.cert_warn_days)


@router.get("/tickets", response_model=list[TicketSummary], tags=["support"])
def tickets(s: Settings = Depends(get_settings)):
    return content.list_tickets(s.tickets_dir)


@router.get("/tickets/{ticket_id}", response_model=Ticket, tags=["support"])
def ticket(ticket_id: str, s: Settings = Depends(get_settings)):
    t = content.get_ticket(s.tickets_dir, ticket_id)
    if not t:
        raise HTTPException(404, "ticket not found")
    return t


@router.get("/scenarios", response_model=list[Scenario], tags=["support"])
def scenarios(s: Settings = Depends(get_settings)):
    return content.list_scenarios(s.scenarios_dir)
