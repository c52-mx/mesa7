import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import type { Option, OptionGroup, Product } from "./api";

export type SelectedOption = { id: number; group: string; name: string; price_delta: string };
export type CartLine = {
  /** Producto + opciones + notas: lo mismo agregado dos veces se junta en una línea. */
  key: string;
  product: Product;
  options: SelectedOption[];
  notes: string;
  quantity: number;
  /** Precio de una pieza con los extras. */
  unitPrice: number;
};
type BranchRef = { id: number; name: string };
type State = { branch: BranchRef | null; lines: CartLine[] };

type CartValue = State & {
  count: number;
  total: number;
  /** Piezas de un producto en el carrito (todas sus variantes). */
  quantityOf: (productId: number) => number;
  add: (
    branch: BranchRef,
    product: Product,
    extras?: { options?: SelectedOption[]; notes?: string; quantity?: number },
  ) => void;
  changeQuantity: (key: string, delta: number) => void;
  clear: () => void;
};

const CartContext = createContext<CartValue | null>(null);

export function useCart(): CartValue {
  const value = useContext(CartContext);
  if (!value) throw new Error("useCart fuera de CartProvider");
  return value;
}

const MAX_PER_LINE = 20; // mismo límite que valida el servidor
const EMPTY: State = { branch: null, lines: [] };

/** Une los grupos del producto con los ids elegidos (ya validados en pantalla). */
export function selectedOptions(groups: OptionGroup[], chosen: Record<number, number[]>): SelectedOption[] {
  return groups.flatMap((group) =>
    (chosen[group.id] ?? [])
      .map((id) => group.options.find((o: Option) => o.id === id))
      .filter((o): o is Option => !!o)
      .map((o) => ({ id: o.id, group: group.name, name: o.name, price_delta: o.price_delta })),
  );
}

export function unitPrice(product: Product, options: SelectedOption[]): number {
  return Number(product.price) + options.reduce((sum, o) => sum + Number(o.price_delta), 0);
}

export function CartProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<State>(EMPTY);

  const add = useCallback<CartValue["add"]>((branch, product, extras = {}) => {
    const options = extras.options ?? [];
    const notes = (extras.notes ?? "").trim();
    const quantity = extras.quantity ?? 1;
    const key = `${product.id}|${options.map((o) => o.id).sort((a, b) => a - b).join(",")}|${notes}`;
    setState((current) => {
      // El carrito es de una sola sucursal: si cambia de sucursal, empieza de cero.
      const lines = current.branch && current.branch.id !== branch.id ? [] : current.lines;
      const exists = lines.some((l) => l.key === key);
      return {
        branch,
        lines: exists
          ? lines.map((l) => (l.key === key ? { ...l, quantity: Math.min(l.quantity + quantity, MAX_PER_LINE) } : l))
          : [...lines, { key, product, options, notes, quantity: Math.min(quantity, MAX_PER_LINE), unitPrice: unitPrice(product, options) }],
      };
    });
  }, []);

  const changeQuantity = useCallback((key: string, delta: number) => {
    setState((current) => {
      const lines = current.lines.flatMap((l) => {
        if (l.key !== key) return [l];
        const quantity = Math.min(l.quantity + delta, MAX_PER_LINE);
        return quantity > 0 ? [{ ...l, quantity }] : [];
      });
      return lines.length ? { ...current, lines } : EMPTY;
    });
  }, []);

  const clear = useCallback(() => setState(EMPTY), []);

  const value = useMemo<CartValue>(
    () => ({
      ...state,
      count: state.lines.reduce((n, l) => n + l.quantity, 0),
      total: state.lines.reduce((sum, l) => sum + l.unitPrice * l.quantity, 0),
      quantityOf: (id) => state.lines.filter((l) => l.product.id === id).reduce((n, l) => n + l.quantity, 0),
      add,
      changeQuantity,
      clear,
    }),
    [state, add, changeQuantity, clear],
  );
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}
