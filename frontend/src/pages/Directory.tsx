import { Group, User } from "../api/client";
import { ErrorBanner, Pill } from "../components/ui";
import { usePoll } from "../hooks/usePoll";

export default function Directory() {
  const users = usePoll<User[]>("/directory/users");
  const groups = usePoll<Group[]>("/directory/groups");
  return (
    <>
      <h1>Directory</h1>
      <p className="sub">Read live from OpenLDAP. Keycloak and the proxy use these same users and groups.</p>
      <ErrorBanner error={users.error ?? groups.error} />
      <div className="grid cols-2">
        <div className="card table-wrap">
          <h2>Users</h2>
          <table>
            <thead><tr><th>User</th><th>Name</th><th>Title</th><th>Groups</th></tr></thead>
            <tbody>{(users.data ?? []).map((u) => (
              <tr key={u.uid}><td className="mono">{u.uid}</td><td>{u.name}<div className="muted">{u.email}</div></td><td>{u.title}</td>
                <td>{u.groups.map((g) => <span key={g} style={{ marginRight: 4 }}><Pill kind="group">{g}</Pill></span>)}</td></tr>
            ))}</tbody>
          </table>
        </div>
        <div className="card table-wrap">
          <h2>Groups and policy effect</h2>
          <table>
            <thead><tr><th>Group</th><th>Members</th><th>What it controls</th></tr></thead>
            <tbody>{(groups.data ?? []).map((g) => (
              <tr key={g.name}><td className="mono">{g.name}</td><td>{g.members.join(", ")}</td><td>{EFFECT[g.name] ?? "–"}</td></tr>
            ))}</tbody>
          </table>
        </div>
      </div>
    </>
  );
}

const EFFECT: Record<string, string> = {
  "zg-admins": "Access to this console and the app's /admin area",
  contractors: "Social media blocked at the web gateway",
  finance: "Standard employee web policy",
  engineering: "Standard employee web policy",
};
