import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { initAuth } from "./auth";
import "./styles/app.css";

const root = createRoot(document.getElementById("root")!);
root.render(<div className="center"><p className="sub">Signing in…</p></div>);

initAuth()
  .then((session) => {
    if (session === "redirecting") return;
    root.render(<React.StrictMode><BrowserRouter><App session={session} /></BrowserRouter></React.StrictMode>);
  })
  .catch((e: Error) => {
    root.render(<div className="center"><div><h1>Cannot sign in</h1><p className="sub">{e.message}. Check that Keycloak and the API are running.</p></div></div>);
  });
