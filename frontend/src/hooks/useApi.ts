import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/utils";

export function useQuery<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api<T>(path);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [path]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

export function usePolling<T>(path: string, intervalMs: number, shouldPoll: boolean) {
  const { data, loading, error, refetch } = useQuery<T>(path);

  useEffect(() => {
    if (!shouldPoll) return;
    const id = setInterval(refetch, intervalMs);
    return () => clearInterval(id);
  }, [shouldPoll, intervalMs, refetch]);

  return { data, loading, error, refetch };
}
