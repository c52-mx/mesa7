import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import type { Product } from "./api";

export type CartLine = { product: Product; quantity: number };
type BranchRef = { id: number; name: string };
type State = { branch: BranchRef | null; lines: CartLine[] };

type CartValue = State & {
  count: number;
  total: number;
  quantityOf: (productId: number) => number;
  add: (branch: BranchRef, product: Product) => void;
  remove: (productId: number) => void;
  clear: () => void;
};

const CartContext = createContext<CartValue | null>(null);

export function useCart(): CartValue {
  const value = useContext(CartContext);
  if (!value) throw new Error("useCart fuera de CartProvider");
  return value;
}

const MAX_PER_PRODUCT = 20; // mismo límite que valida el servidor
const EMPTY: State = { branch: null, lines: [] };

export function CartProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<State>(EMPTY);

  const add = useCallback((branch: BranchRef, product: Product) => {
    setState((current) => {
      // El carrito es de una sola sucursal: si cambia de sucursal, empieza de cero.
      const lines = current.branch && current.branch.id !== branch.id ? [] : current.lines;
      const exists = lines.some((l) => l.product.id === product.id);
      return {
        branch,
        lines: exists
          ? lines.map((l) =>
              l.product.id === product.id
                ? { ...l, quantity: Math.min(l.quantity + 1, MAX_PER_PRODUCT) }
                : l,
            )
          : [...lines, { product, quantity: 1 }],
      };
    });
  }, []);

  const remove = useCallback((productId: number) => {
    setState((current) => {
      const lines = current.lines.flatMap((l) =>
        l.product.id !== productId ? [l] : l.quantity > 1 ? [{ ...l, quantity: l.quantity - 1 }] : [],
      );
      return lines.length ? { ...current, lines } : EMPTY;
    });
  }, []);

  const clear = useCallback(() => setState(EMPTY), []);

  const value = useMemo<CartValue>(
    () => ({
      ...state,
      count: state.lines.reduce((n, l) => n + l.quantity, 0),
      total: state.lines.reduce((sum, l) => sum + Number(l.product.price) * l.quantity, 0),
      quantityOf: (id) => state.lines.find((l) => l.product.id === id)?.quantity ?? 0,
      add,
      remove,
      clear,
    }),
    [state, add, remove, clear],
  );
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}
