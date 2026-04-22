import { useEffect, useState } from "react";

export function usePolling<T>(loader: () => Promise<T>, interval = 8000) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    let inFlight = false;
    let timeoutId: number | null = null;

    setLoading(true);

    const tick = async () => {
      if (!active || inFlight) {
        return;
      }
      inFlight = true;
      try {
        const next = await loader();
        if (active) {
          setData(next);
          setError(null);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Unexpected error");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
        inFlight = false;
        if (active && interval > 0) {
          timeoutId = window.setTimeout(() => {
            void tick();
          }, interval);
        }
      }
    };

    void tick();
    return () => {
      active = false;
      if (timeoutId !== null) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [interval, loader]);

  return { data, error, loading };
}
