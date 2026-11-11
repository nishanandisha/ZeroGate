from typing import Literal

from pydantic import BaseModel

Status = Literal["up", "degraded", "down"]


class ComponentHealth(BaseModel):
    id: str
    name: str
    category: str
    status: Status
    latency_ms: float | None = None
    detail: str = ""
    data: dict = {}
    checked_at: float


class User(BaseModel):
    uid: str
    name: str
    email: str | None = None
    title: str | None = None
    groups: list[str] = []


class Group(BaseModel):
    name: str
    members: list[str] = []


class TrafficEvent(BaseModel):
    ts: float
    source: Literal["swg", "dlp"]
    user: str | None = None
    client: str | None = None
    method: str
    host: str | None = None
    url: str
    status: int | None = None
    bytes: int = 0
    action: str
    inspection: str | None = None
    rules: list[str] = []


class CertInfo(BaseModel):
    file: str
    subject: str
    issuer: str
    serial: str
    not_before: str
    not_after: str
    days_left: int
    is_ca: bool
    san: list[str] = []
    status: Status


class TicketSummary(BaseModel):
    id: str
    title: str
    severity: str | None = None
    component: str | None = None
    status: str | None = None
    scenario: str | None = None


class Ticket(TicketSummary):
    markdown: str


class Scenario(BaseModel):
    id: str
    title: str
    ticket: str
    component: str
    summary: str
