import { Stepper } from "@/components/stepper";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Text } from "@/components/ui/text";
import { api, errorMessage, type Menu } from "@/lib/api";
import { useCart } from "@/lib/cart";
import { money } from "@/lib/format";
import { Link, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, View } from "react-native";

export default function BranchMenu() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const cart = useCart();
  const [menu, setMenu] = useState<Menu | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setMenu(null);
    try {
      setMenu(await api<Menu>(`/api/branches/${id}/menu/`));
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  useEffect(() => {
    load();
  }, [id]);

  if (error) {
    return (
      <View className="flex-1 items-center justify-center gap-4 bg-background p-6">
        <Text className="text-center text-destructive">{error}</Text>
        <Button onPress={load}>
          <Text>Reintentar</Text>
        </Button>
      </View>
    );
  }
  if (!menu) {
    return (
      <View className="flex-1 items-center justify-center bg-background">
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <View className="flex-1 bg-background">
      <ScrollView contentContainerClassName="items-center p-4 pb-28">
        <View className="w-full max-w-md gap-6">
          <Text className="text-xl font-semibold">{menu.branch.name}</Text>
          {menu.categories.length === 0 ? (
            <Text className="text-muted-foreground">Por ahora no hay productos disponibles en esta sucursal.</Text>
          ) : null}
          {menu.categories.map((category) => (
            <View key={category.id} className="gap-3">
              <Text className="text-lg font-semibold">{category.name}</Text>
              {category.products.map((product) => (
                <Card key={product.id}>
                  <CardContent className="flex-row items-center justify-between gap-3 pt-6">
                    <View className="flex-1 gap-1">
                      <Text className="font-semibold">{product.name}</Text>
                      {product.description ? (
                        <Text className="text-sm text-muted-foreground">{product.description}</Text>
                      ) : null}
                      <Text className="font-medium">{money(product.price)}</Text>
                    </View>
                    <Stepper
                      quantity={cart.quantityOf(product.id)}
                      onAdd={() => cart.add(menu.branch, product)}
                      onRemove={() => cart.remove(product.id)}
                    />
                  </CardContent>
                </Card>
              ))}
            </View>
          ))}
        </View>
      </ScrollView>

      {cart.count > 0 && cart.branch?.id === menu.branch.id ? (
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
      ) : null}
    </View>
  );
}
