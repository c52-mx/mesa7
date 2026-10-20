import type { Product } from "@/lib/api";
import { useAddProduct, useOpenProduct } from "@/lib/add-product";
import { useCart } from "@/lib/cart";
import { money } from "@/lib/format";
import { Pressable, View } from "react-native";

import { AddButton } from "./add-button";
import { ProductThumb } from "./product-thumb";
import { Text } from "./ui/text";

type Branch = { id: number; name: string };

/** Fila de menú estilo Uber Eats: texto a la izquierda, foto con botón "+" a la derecha. */
export function ProductRow({ branch, product }: { branch: Branch; product: Product }) {
  const cart = useCart();
  const add = useAddProduct();
  const open = useOpenProduct();
  const hasOptions = product.option_groups.length > 0;

  return (
    <Pressable
      onPress={() => open(branch, product)}
      accessibilityRole="button"
      className="flex-row items-center gap-4 border-b border-border py-4"
    >
      <View className="flex-1 gap-1">
        <Text className="text-base font-semibold">{product.name}</Text>
        {product.description ? (
          <Text className="text-sm text-muted-foreground" numberOfLines={2}>
            {product.description}
          </Text>
        ) : null}
        <Text className="font-medium">{hasOptions ? "Desde " : ""}{money(product.price)}</Text>
      </View>
      <View>
        <ProductThumb product={product} size={96} />
        <View className="absolute -bottom-2 -right-2">
          <AddButton
            quantity={cart.quantityOf(product.id)}
            onPress={() => add(branch, product)}
            label={hasOptions ? `Personalizar ${product.name}` : `Agregar ${product.name}`}
          />
        </View>
      </View>
    </Pressable>
  );
}
