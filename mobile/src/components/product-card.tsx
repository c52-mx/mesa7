import type { Product } from "@/lib/api";
import { useAddProduct, useOpenProduct } from "@/lib/add-product";
import { useCart } from "@/lib/cart";
import { money } from "@/lib/format";
import { Pressable, View } from "react-native";

import { AddButton } from "./add-button";
import { ProductThumb } from "./product-thumb";
import { Text } from "./ui/text";

type Branch = { id: number; name: string };

/** Tarjeta vertical con foto grande, para carruseles (Destacados e Inicio). */
export function ProductCard({ branch, product }: { branch: Branch; product: Product }) {
  const cart = useCart();
  const add = useAddProduct();
  const open = useOpenProduct();
  const hasOptions = product.option_groups.length > 0;

  return (
    <Pressable
      onPress={() => open(branch, product)}
      accessibilityRole="button"
      className="w-40 gap-2 rounded-2xl border border-border bg-card p-2"
    >
      <View>
        <ProductThumb product={product} className="aspect-square w-full" />
        <View className="absolute bottom-2 right-2">
          <AddButton
            quantity={cart.quantityOf(product.id)}
            onPress={() => add(branch, product)}
            label={hasOptions ? `Personalizar ${product.name}` : `Agregar ${product.name}`}
          />
        </View>
      </View>
      <View className="gap-0.5 px-1 pb-1">
        <Text className="font-semibold" numberOfLines={2}>
          {product.name}
        </Text>
        <Text className="text-sm text-muted-foreground">{money(product.price)}</Text>
      </View>
    </Pressable>
  );
}
