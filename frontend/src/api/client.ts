export type Status = "up" | "degraded" | "down";
export interface ComponentHealth { id: string; name: string; category: string; status: Status; latency_ms: number | null; detail: string; data: Record<string, unknown>; checked_at: number }
export interface User { uid: string; name: string; email?: string; title?: string; groups: string[] }
export interface Group { name: string; members: string[] }
export interface TrafficEvent { ts: number; source: "swg" | "dlp"; user?: string; client?: string; method: string; host?: string; url: string; status?: number; bytes: number; action: string; inspection?: string; rules: string[] }
export interface TrafficStats { total: number; blocked: number; bytes: number; by_action: Record<string, number>; by_inspection: Record<string, number>; top_hosts: [string, number][]; top_users: [string, number][]; dlp_rules: Record<string, number> }
export interface CertInfo { file: string; subject: string; issuer: string; serial: string; not_before: string; not_after: string; days_left: number; is_ca: boolean; san: string[]; status: Status }
export interface TicketSummary { id: string; title: string; severity?: string; component?: string; status?: string; scenario?: string }
export interface Ticket extends TicketSummary { markdown: string }
export interface Scenario { id: string; title: string; ticket: string; component: string; summary: string }
export interface AuthConfig { enabled: boolean; authority: string; client_id: string; admin_group: string }

let tokenProvider: () => string | null = () => null;
export const setTokenProvider = (fn: () => string | null) => { tokenProvider = fn; };

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export async function api<T>(path: string): Promise<T> {
  const token = tokenProvider();
  const res = await fetch(`/api${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail ?? detail; } catch { /* non-JSON error body */ }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}
