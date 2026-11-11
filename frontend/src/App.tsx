import { NavLink, Route, Routes } from "react-router-dom";
import { Session } from "./auth";
import Certificates from "./pages/Certificates";
import Dashboard from "./pages/Dashboard";
import Directory from "./pages/Directory";
import Tickets from "./pages/Tickets";
import Traffic from "./pages/Traffic";

export default function App({ session }: { session: Session }) {
  if (!session.isAdmin) {
    return (
      <div className="center">
        <div>
          <h1>Access denied</h1>
          <p className="sub">You are signed in as <b>{session.username}</b>, but this console needs the <code>zg-admins</code> group.</p>
          <button onClick={session.logout}>Sign out</button>
        </div>
      </div>
    );
  }
  return (
    <div className="shell">
      <nav className="side">
        <div className="brand">ZeroGate<small>Zero-trust access lab</small></div>
        <NavLink to="/" end>Overview</NavLink>
        <NavLink to="/traffic">Traffic</NavLink>
        <NavLink to="/directory">Directory</NavLink>
        <NavLink to="/certificates">Certificates</NavLink>
        <NavLink to="/tickets">Support tickets</NavLink>
        <div className="who"><span>Signed in as <b>{session.username}</b></span><br /><button onClick={session.logout}>Sign out</button></div>
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/traffic" element={<Traffic />} />
          <Route path="/directory" element={<Directory />} />
          <Route path="/certificates" element={<Certificates />} />
          <Route path="/tickets" element={<Tickets />} />
          <Route path="*" element={<Dashboard />} />
        </Routes>
      </main>
    </div>
  );
}
