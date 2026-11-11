import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";

/** Fetch `path` now and every `intervalMs` (0 = once). Keeps the last good data while a refresh fails. */
export function usePoll<T>(path: string, intervalMs = 0) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [updated, setUpdated] = useState<number | null>(null);
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    const load = () =>
      api<T>(path)
        .then((d) => { if (alive.current) { setData(d); setError(null); setUpdated(Date.now()); } })
        .catch((e: Error) => { if (alive.current) setError(e.message); });
    void load();
    const id = intervalMs ? window.setInterval(load, intervalMs) : 0;
    return () => { alive.current = false; if (id) window.clearInterval(id); };
  }, [path, intervalMs]);

  return { data, error, updated };
}
