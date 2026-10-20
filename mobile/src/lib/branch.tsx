import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api, errorMessage, type Branch } from "./api";
import { storage } from "./storage";

const KEY = "branch_id";

type BranchValue = {
  branches: Branch[];
  /** Sucursal elegida (la última usada, o la primera). null mientras carga o si no hay sucursales. */
  selected: Branch | null;
  loading: boolean;
  error: string | null;
  select: (id: number) => void;
  reload: () => Promise<void>;
};

const BranchContext = createContext<BranchValue | null>(null);

export function useBranches(): BranchValue {
  const value = useContext(BranchContext);
  if (!value) throw new Error("useBranches fuera de BranchProvider");
  return value;
}

export function BranchProvider({ children }: { children: ReactNode }) {
  const [branches, setBranches] = useState<Branch[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setError(null);
    try {
      setBranches(await api<Branch[]>("/api/branches/"));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    storage
      .get(KEY)
      .then((saved) => saved && setSelectedId(Number(saved)))
      .catch(() => {});
    reload();
  }, [reload]);

  const select = useCallback((id: number) => {
    setSelectedId(id);
    storage.set(KEY, String(id)).catch(() => {});
  }, []);

  const value = useMemo<BranchValue>(
    () => ({
      branches,
      selected: branches.find((b) => b.id === selectedId) ?? branches[0] ?? null,
      loading,
      error,
      select,
      reload,
    }),
    [branches, selectedId, loading, error, select, reload],
  );
  return <BranchContext.Provider value={value}>{children}</BranchContext.Provider>;
}
