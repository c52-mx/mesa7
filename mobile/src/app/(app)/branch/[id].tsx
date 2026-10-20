import { CartBar } from "@/components/cart-bar";
import { ProductCard } from "@/components/product-card";
import { ProductRow } from "@/components/product-row";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Text } from "@/components/ui/text";
import type { Menu } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, View } from "react-native";

export default function BranchMenu() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data: menu, error, reload } = useApi<Menu>(`/api/branches/${id}/menu/`);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<number | null>(null);

  if (!menu) {
    return (
      <View className="flex-1 items-center justify-center gap-4 bg-background p-6">
        {error ? (
          <>
            <Text className="text-center text-destructive">{error}</Text>
            <Button onPress={reload}>
              <Text>Reintentar</Text>
            </Button>
          </>
        ) : (
          <ActivityIndicator />
        )}
      </View>
    );
  }

  const branch = menu.branch;
  const q = query.trim().toLowerCase();
  const all = menu.categories.flatMap((c) => c.products);
  const featured = all.filter((p) => p.is_featured);
  const matches = q ? all.filter((p) => `${p.name} ${p.description}`.toLowerCase().includes(q)) : [];
  const visible = menu.categories.filter((c) => category === null || c.id === category);

  return (
    <View className="flex-1 bg-background">
      <ScrollView contentContainerClassName="items-center pb-28" keyboardShouldPersistTaps="handled">
        <View className="w-full max-w-md gap-5 p-4">
          <Input
            value={query}
            onChangeText={setQuery}
            placeholder="Buscar en el menú"
            accessibilityLabel="Buscar en el menú"
            returnKeyType="search"
          />

          {menu.categories.length > 1 && !q ? (
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8 }}>
              {[{ id: null, name: "Todo" }, ...menu.categories].map((c) => {
                const active = c.id === category;
                return (
                  <Pressable
                    key={String(c.id)}
                    onPress={() => setCategory(c.id)}
                    accessibilityRole="button"
                    className={active ? "rounded-full bg-primary px-4 py-2" : "rounded-full border border-border bg-card px-4 py-2"}
                  >
                    <Text className={active ? "font-medium text-primary-foreground" : "font-medium"}>{c.name}</Text>
                  </Pressable>
                );
              })}
            </ScrollView>
          ) : null}

          {all.length === 0 ? (
            <Text className="text-muted-foreground">Por ahora no hay productos disponibles en esta sucursal.</Text>
          ) : null}

          {q ? (
            <View>
              <Text className="mb-1 text-lg font-semibold">Resultados</Text>
              {matches.length === 0 ? <Text className="py-4 text-muted-foreground">No encontramos «{query.trim()}».</Text> : null}
              {matches.map((product) => (
                <ProductRow key={product.id} branch={branch} product={product} />
              ))}
            </View>
          ) : (
            <>
              {category === null && featured.length > 0 ? (
                <View className="gap-3">
                  <Text className="text-xl font-bold">Destacados</Text>
                  <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 12 }}>
                    {featured.map((product) => (
                      <ProductCard key={product.id} branch={branch} product={product} />
                    ))}
                  </ScrollView>
                </View>
              ) : null}
              {visible.map((c) => (
                <View key={c.id}>
                  <Text className="text-xl font-bold">{c.name}</Text>
                  {c.products.map((product) => (
                    <ProductRow key={product.id} branch={branch} product={product} />
                  ))}
                </View>
              ))}
            </>
          )}
        </View>
      </ScrollView>

      <CartBar branchId={branch.id} />
    </View>
  );
}
