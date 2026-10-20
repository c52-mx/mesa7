import { useFocusEffect } from "expo-router";
import { useCallback, useState } from "react";

import { api, errorMessage } from "./api";

type State<T> = { data: T | null; error: string | null; loading: boolean; reload: () => Promise<void> };

/**
 * Carga un GET autenticado y lo recarga cada vez que la pantalla vuelve a tener foco.
 * Si `path` es null no hace nada (por ejemplo, mientras falta la sucursal elegida).
 */
export function useApi<T>(path: string | null): State<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(path !== null);

  const reload = useCallback(async () => {
    if (path === null) {
      setData(null);
      setLoading(false);
      return;
    }
    setError(null);
    try {
      setData(await api<T>(path));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [path]);

  useFocusEffect(
    useCallback(() => {
      reload();
    }, [reload]),
  );

  return { data, error, loading, reload };
}
