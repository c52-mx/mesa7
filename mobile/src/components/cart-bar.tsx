import { useCart } from "@/lib/cart";
import { money } from "@/lib/format";
import { Link } from "expo-router";
import { View } from "react-native";

import { Button } from "./ui/button";
import { Text } from "./ui/text";

/** Barra flotante "Ver pedido · n · $total". Con `branchId` solo aparece si el carrito es de esa sucursal. */
export function CartBar({ branchId }: { branchId?: number }) {
  const cart = useCart();
  if (cart.count === 0 || (branchId !== undefined && cart.branch?.id !== branchId)) return null;
  return (
    <View className="absolute bottom-0 left-0 right-0 items-center border-t border-border bg-background p-4">
      <View className="w-full max-w-md">
        <Link href="/cart" asChild>
          <Button size="lg">
            <Text>
              Ver pedido · {cart.count} · {money(cart.total)}
            </Text>
          </Button>
        </Link>
      </View>
    </View>
  );
}
