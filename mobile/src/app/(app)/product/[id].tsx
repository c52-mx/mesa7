import { BottomBar } from "@/components/bottom-bar";
import { KeyboardScrollView } from "@/components/keyboard-scroll-view";
import { ProductThumb } from "@/components/product-thumb";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Text } from "@/components/ui/text";
import type { Menu, OptionGroup } from "@/lib/api";
import { usePalette } from "@/lib/brand-provider";
import { selectedOptions, unitPrice, useCart } from "@/lib/cart";
import { money } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import Ionicons from "@expo/vector-icons/Ionicons";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { ActivityIndicator, Pressable, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

function ruleText(group: OptionGroup): string {
  if (group.max_select === 1) return "Elegir 1";
  return group.required > 0 ? `Elige de ${group.required} a ${group.max_select}` : `Selecciona hasta ${group.max_select}`;
}

export default function ProductDetail() {
  const { id, branch } = useLocalSearchParams<{ id: string; branch: string }>();
  const router = useRouter();
  const cart = useCart();
  const palette = usePalette();
  const insets = useSafeAreaInsets();
  const { data: menu, error } = useApi<Menu>(`/api/branches/${branch}/menu/`);
  const [chosen, setChosen] = useState<Record<number, number[]>>({});
  const [notes, setNotes] = useState("");
  const [quantity, setQuantity] = useState(1);

  const product = menu?.categories.flatMap((c) => c.products).find((p) => p.id === Number(id));

  if (!menu || !product) {
    return (
      <View className="flex-1 items-center justify-center gap-3 bg-background p-6">
        {error || menu ? (
          <Text className="text-center text-muted-foreground">{error ?? "Este producto ya no está disponible."}</Text>
        ) : (
          <ActivityIndicator />
        )}
      </View>
    );
  }

  const count = (group: OptionGroup) => (chosen[group.id] ?? []).length;
  const missing = product.option_groups.filter((g) => count(g) < g.required);
  const options = selectedOptions(product.option_groups, chosen);
  const total = unitPrice(product, options) * quantity;

  function toggle(group: OptionGroup, optionId: number) {
    setChosen((current) => {
      const selected = current[group.id] ?? [];
      const isOn = selected.includes(optionId);
      if (group.max_select === 1) {
        // Radio: elegir otra cambia; tocar la elegida solo la quita si el grupo es opcional.
        if (isOn) return group.required === 0 ? { ...current, [group.id]: [] } : current;
        return { ...current, [group.id]: [optionId] };
      }
      if (isOn) return { ...current, [group.id]: selected.filter((i) => i !== optionId) };
      if (selected.length >= group.max_select) return current;
      return { ...current, [group.id]: [...selected, optionId] };
    });
  }

  function addToCart() {
    cart.add(menu!.branch, product!, { options, notes, quantity });
    router.back();
  }

  return (
    <View className="flex-1 bg-background">
      <KeyboardScrollView
        contentContainerClassName="items-center"
        bottomPadding={170 + insets.bottom}
        scrollToEndOnKeyboard
      >
        <View className="w-full max-w-md gap-6 p-4">
          <ProductThumb product={product} className="aspect-video w-full" />
          <View className="gap-1">
            <Text className="text-2xl font-bold">{product.name}</Text>
            <Text className="text-lg font-semibold">{money(product.price)}</Text>
            {product.description ? <Text className="text-muted-foreground">{product.description}</Text> : null}
          </View>

          {product.option_groups.map((group) => (
            <View key={group.id} className="gap-1">
              <View className="flex-row items-start justify-between gap-3">
                <View className="flex-1">
                  <Text className="text-lg font-semibold">{group.name}</Text>
                  <Text className="text-sm text-muted-foreground">{ruleText(group)}</Text>
                </View>
                <Badge variant={group.required > 0 ? "secondary" : "outline"}>
                  <Text>{group.required > 0 ? "Obligatorio" : "Opcional"}</Text>
                </Badge>
              </View>
              {group.options.map((option) => {
                const on = (chosen[group.id] ?? []).includes(option.id);
                const full = !on && group.max_select > 1 && count(group) >= group.max_select;
                const radio = group.max_select === 1;
                return (
                  <Pressable
                    key={option.id}
                    onPress={() => toggle(group, option.id)}
                    disabled={full}
                    accessibilityRole={radio ? "radio" : "checkbox"}
                    accessibilityState={{ checked: on, disabled: full }}
                    className={full ? "flex-row items-center justify-between border-b border-border py-3 opacity-40" : "flex-row items-center justify-between border-b border-border py-3"}
                  >
                    <View className="flex-1 gap-0.5">
                      <Text className="font-medium">{option.name}</Text>
                      {Number(option.price_delta) > 0 ? (
                        <Text className="text-sm text-muted-foreground">+{money(option.price_delta)}</Text>
                      ) : null}
                      {option.is_popular ? <Text className="text-sm font-medium text-primary">Popular</Text> : null}
                    </View>
                    <Ionicons
                      name={radio ? (on ? "radio-button-on" : "radio-button-off") : on ? "checkbox" : "square-outline"}
                      size={24}
                      color={on ? palette.primary : palette.mutedForeground}
                    />
                  </Pressable>
                );
              })}
            </View>
          ))}

          <View className="gap-2">
            <Text className="text-lg font-semibold">Instrucciones especiales</Text>
            <Input
              value={notes}
              onChangeText={setNotes}
              maxLength={200}
              multiline
              placeholder="Alergias, sin hielo, bien caliente..."
              accessibilityLabel="Instrucciones especiales"
            />
            <Text className="text-xs text-muted-foreground">
              La tienda hará lo posible, pero no puede garantizar solicitudes por alergias.
            </Text>
          </View>
        </View>
      </KeyboardScrollView>

      <BottomBar>
        {missing.length > 0 ? (
          <Text className="text-center text-sm text-muted-foreground">
            Falta elegir: {missing.map((g) => g.name).join(", ")}
          </Text>
        ) : null}
        <View className="flex-row items-center gap-3">
          <View className="flex-row items-center gap-3">
            <Button size="icon" variant="outline" onPress={() => setQuantity((q) => Math.max(1, q - 1))} accessibilityLabel="Quitar uno">
              <Text>−</Text>
            </Button>
            <Text className="w-6 text-center text-lg font-semibold">{quantity}</Text>
            <Button size="icon" variant="outline" onPress={() => setQuantity((q) => Math.min(20, q + 1))} accessibilityLabel="Agregar uno">
              <Text>+</Text>
            </Button>
          </View>
          <View className="flex-1">
            <Button size="lg" disabled={missing.length > 0} onPress={addToCart}>
              <Text>Agregar · {money(total)}</Text>
            </Button>
          </View>
        </View>
      </BottomBar>
    </View>
  );
}
