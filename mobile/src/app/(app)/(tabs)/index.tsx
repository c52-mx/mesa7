import { BannerCarousel } from "@/components/banner-carousel";
import { BranchPicker } from "@/components/branch-picker";
import { CartBar } from "@/components/cart-bar";
import { ProgressBar } from "@/components/progress-bar";
import { Stepper } from "@/components/stepper";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Text } from "@/components/ui/text";
import type { Banner, Loyalty, Me, Menu } from "@/lib/api";
import { useBranches } from "@/lib/branch";
import { useBrand } from "@/lib/brand-provider";
import { useCart } from "@/lib/cart";
import { money } from "@/lib/format";
import { rewardProgress } from "@/lib/loyalty";
import { useApi } from "@/lib/use-api";
import { Link, useRouter } from "expo-router";
import { useState } from "react";
import { Pressable, ScrollView, View } from "react-native";

function firstName(me: Me | null): string {
  if (!me) return "";
  return (me.full_name || me.email.split("@")[0]).split(" ")[0];
}

export default function Home() {
  const router = useRouter();
  const brand = useBrand();
  const cart = useCart();
  const { selected, loading: loadingBranches, error: branchError, reload } = useBranches();
  const [category, setCategory] = useState<number | null>(null);

  const me = useApi<Me>("/api/me/").data;
  const banners = useApi<Banner[]>("/api/banners/").data ?? [];
  const loyalty = useApi<Loyalty>(brand.loyalty_enabled ? "/api/loyalty/" : null).data;
  const menu = useApi<Menu>(selected ? `/api/branches/${selected.id}/menu/` : null).data;

  const categories = menu?.categories ?? [];
  const products = categories
    .filter((c) => category === null || c.id === category)
    .flatMap((c) => c.products)
    .slice(0, 12);

  return (
    <View className="flex-1 bg-background">
      <ScrollView contentContainerClassName="items-center px-4 pb-28 pt-14">
        <View className="w-full max-w-md gap-6">
          <View className="gap-4">
            <View className="gap-1">
              <Text className="text-xs uppercase tracking-widest text-muted-foreground">Bienvenido</Text>
              <Text className="text-3xl font-bold">Hola{me ? `, ${firstName(me)}` : ""}</Text>
            </View>
            <BranchPicker />
          </View>

          {loyalty ? (
            <Link href="/card" asChild>
              <Pressable accessibilityRole="button">
                <Card>
                  <CardContent className="gap-3 pt-6">
                    <Text className="text-xs uppercase tracking-widest text-muted-foreground">Mis puntos</Text>
                    <View className="flex-row items-end gap-2">
                      <Text className="text-4xl font-bold">{loyalty.points}</Text>
                      <Text className="pb-1 text-muted-foreground">puntos</Text>
                    </View>
                    <ProgressBar value={rewardProgress(loyalty)} />
                    <Text className="text-sm text-muted-foreground">
                      {loyalty.next_reward
                        ? `Te faltan ${loyalty.next_reward.missing} para: ${loyalty.next_reward.name}`
                        : "¡Desbloqueaste todas las recompensas!"}
                    </Text>
                  </CardContent>
                </Card>
              </Pressable>
            </Link>
          ) : null}

          <BannerCarousel banners={banners} />

          <View className="gap-3">
            <View className="flex-row items-center justify-between">
              <Text className="text-xs uppercase tracking-widest text-muted-foreground">Disponible en sucursal</Text>
              {selected ? (
                <Link href={`/branch/${selected.id}`} asChild>
                  <Pressable accessibilityRole="button">
                    <Text className="text-sm font-semibold text-primary">Ver todo</Text>
                  </Pressable>
                </Link>
              ) : null}
            </View>

            {branchError ? (
              <View className="items-center gap-3 py-4">
                <Text className="text-center text-destructive">{branchError}</Text>
                <Button onPress={reload}>
                  <Text>Reintentar</Text>
                </Button>
              </View>
            ) : null}
            {!loadingBranches && !branchError && !selected ? (
              <Text className="text-muted-foreground">Este negocio aún no tiene sucursales activas.</Text>
            ) : null}

            {categories.length > 1 ? (
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8 }}>
                {[{ id: null, name: "Todo" }, ...categories].map((c) => {
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

            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 12 }}>
              {products.map((product) => (
                <Card key={product.id} className="w-44">
                  <CardContent className="justify-between gap-3 pt-5">
                    <View className="gap-1">
                      <Text className="font-semibold" numberOfLines={2}>
                        {product.name}
                      </Text>
                      <Text className="font-medium text-muted-foreground">{money(product.price)}</Text>
                    </View>
                    <View className="items-start">
                      <Stepper
                        quantity={cart.quantityOf(product.id)}
                        onAdd={() => selected && cart.add({ id: selected.id, name: selected.name }, product)}
                        onRemove={() => cart.remove(product.id)}
                      />
                    </View>
                  </CardContent>
                </Card>
              ))}
            </ScrollView>
          </View>

          {selected ? (
            <Button size="lg" onPress={() => router.push(`/branch/${selected.id}`)}>
              <Text>Ordena ahora</Text>
            </Button>
          ) : null}
        </View>
      </ScrollView>
      <CartBar />
    </View>
  );
}
