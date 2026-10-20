import { useCart } from "@/lib/cart";
import { money } from "@/lib/format";
import { Link } from "expo-router";

import { BottomBar } from "./bottom-bar";
import { Button } from "./ui/button";
import { Text } from "./ui/text";

/** Barra flotante "Ver pedido · n · $total". Con `branchId` solo aparece si el carrito es de esa sucursal. */
export function CartBar({ branchId, inset }: { branchId?: number; inset?: boolean }) {
  const cart = useCart();
  if (cart.count === 0 || (branchId !== undefined && cart.branch?.id !== branchId)) return null;
  return (
    <BottomBar inset={inset}>
      <Link href="/cart" asChild>
        <Button size="lg">
          <Text>
            Ver pedido · {cart.count} · {money(cart.total)}
          </Text>
        </Button>
      </Link>
    </BottomBar>
  );
}
