import { useRouter } from "expo-router";
import { useCallback } from "react";

import type { Product } from "./api";
import { useCart } from "./cart";

type BranchRef = { id: number; name: string };

/**
 * Acción del botón "+": un producto sin opciones se agrega directo;
 * uno con opciones abre su detalle para elegirlas (hay grupos obligatorios).
 */
export function useAddProduct() {
  const router = useRouter();
  const cart = useCart();
  return useCallback(
    (branch: BranchRef, product: Product) => {
      if (product.option_groups.length === 0) cart.add(branch, product);
      else router.push({ pathname: "/product/[id]", params: { id: String(product.id), branch: String(branch.id) } });
    },
    [cart, router],
  );
}

export function useOpenProduct() {
  const router = useRouter();
  return useCallback(
    (branch: BranchRef, product: Product) =>
      router.push({ pathname: "/product/[id]", params: { id: String(product.id), branch: String(branch.id) } }),
    [router],
  );
}
