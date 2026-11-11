"""Support tickets (markdown) and break/fix scenarios (scenario.json) from the repo."""
import json
import re
from pathlib import Path

from app.schemas.models import Scenario, Ticket, TicketSummary

_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$")


def _parse_ticket(path: Path) -> Ticket:
    md = path.read_text(encoding="utf-8")
    title_line = next((ln for ln in md.splitlines() if ln.startswith("# ")), f"# {path.stem}")
    tid, _, title = title_line[2:].partition(":")
    meta = {m.group(1).lower(): m.group(2) for ln in md.splitlines()[:20] if (m := _ROW.match(ln))}
    return Ticket(id=tid.strip(), title=title.strip() or tid.strip(), severity=meta.get("severity"),
                  component=meta.get("component"), status=meta.get("status"), scenario=meta.get("scenario"),
                  markdown=md)


def list_tickets(tickets_dir: str) -> list[TicketSummary]:
    files = sorted(Path(tickets_dir, "resolved").glob("TKT-*.md"))
    return [TicketSummary(**_parse_ticket(f).model_dump(exclude={"markdown"})) for f in files]


def get_ticket(tickets_dir: str, ticket_id: str) -> Ticket | None:
    if not re.fullmatch(r"TKT-\d{3}", ticket_id):  # no path traversal
        return None
    matches = list(Path(tickets_dir, "resolved").glob(f"{ticket_id}*.md"))
    return _parse_ticket(matches[0]) if matches else None


def list_scenarios(scenarios_dir: str) -> list[Scenario]:
    out = []
    for f in sorted(Path(scenarios_dir).glob("*/scenario.json")):
        out.append(Scenario(**json.loads(f.read_text())))
    return out
