from ldap3 import Connection, Server

from app.core.config import Settings
from app.schemas.models import Group, User


def _conn(s: Settings) -> Connection:
    c = Connection(Server(s.ldap_url, connect_timeout=3), s.ldap_bind_dn, s.ldap_bind_password, receive_timeout=5)
    if not c.bind():
        raise ConnectionError(f"LDAP bind failed: {c.result.get('description')}")
    return c


def _uid(dn: str) -> str:
    return dn.split(",", 1)[0].split("=", 1)[1]


def groups(s: Settings) -> list[Group]:
    with _conn(s) as c:
        c.search(f"ou=groups,{s.ldap_base}", "(objectClass=groupOfNames)", attributes=["cn", "member"])
        return sorted((Group(name=str(e.cn), members=sorted(_uid(m) for m in e.member.values)) for e in c.entries),
                      key=lambda g: g.name)


def users(s: Settings) -> list[User]:
    member_of: dict[str, list[str]] = {}
    for g in groups(s):
        for m in g.members:
            member_of.setdefault(m, []).append(g.name)
    with _conn(s) as c:
        c.search(f"ou=people,{s.ldap_base}", "(objectClass=inetOrgPerson)", attributes=["uid", "cn", "mail", "title"])
        out = [User(uid=str(e.uid), name=str(e.cn), email=str(e.mail) if e.mail else None,
                    title=str(e.title) if e.title else None, groups=sorted(member_of.get(str(e.uid), [])))
               for e in c.entries]
    return sorted(out, key=lambda u: u.uid)
