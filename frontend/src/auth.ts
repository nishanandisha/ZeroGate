import { User, UserManager, WebStorageStateStore } from "oidc-client-ts";
import { AuthConfig, setTokenProvider } from "./api/client";

export interface Session { username: string; groups: string[]; isAdmin: boolean; logout: () => void }

/** Authorization Code + PKCE against Keycloak. Tokens live in sessionStorage only (cleared with the tab). */
export async function initAuth(): Promise<Session | "redirecting"> {
  const cfg: AuthConfig = await (await fetch("/api/auth/config")).json();
  if (!cfg.enabled) return { username: "auth-disabled", groups: [cfg.admin_group], isAdmin: true, logout: () => {} };

  const mgr = new UserManager({
    authority: cfg.authority,
    client_id: cfg.client_id,
    redirect_uri: `${location.origin}/callback`,
    post_logout_redirect_uri: `${location.origin}/`,
    response_type: "code",
    scope: "openid profile email",
    userStore: new WebStorageStateStore({ store: sessionStorage }),
    automaticSilentRenew: true,
  });

  let user: User | null;
  if (location.pathname === "/callback") {
    user = await mgr.signinRedirectCallback();
    history.replaceState(null, "", "/");
  } else {
    user = await mgr.getUser();
  }
  if (!user || user.expired) {
    await mgr.signinRedirect();
    return "redirecting";
  }
  let current = user;
  mgr.events.addUserLoaded((u) => { current = u; });
  mgr.events.addAccessTokenExpired(() => { void mgr.signinRedirect(); });
  setTokenProvider(() => current.access_token);

  const groups = (user.profile.groups as string[] | undefined) ?? [];
  return {
    username: user.profile.preferred_username ?? user.profile.sub,
    groups,
    isAdmin: groups.includes(cfg.admin_group),
    logout: () => { void mgr.signoutRedirect(); },
  };
}
