import { KeyboardScrollView } from "@/components/keyboard-scroll-view";
import { ProductThumb } from "@/components/product-thumb";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Text } from "@/components/ui/text";
import { api, errorMessage, type Order } from "@/lib/api";
import { useBranches } from "@/lib/branch";
import { usePalette } from "@/lib/brand-provider";
import { useCart } from "@/lib/cart";
import { money } from "@/lib/format";
import { useOrderAlerts } from "@/lib/order-alerts";
import Ionicons from "@expo/vector-icons/Ionicons";
import { useRouter } from "expo-router";
import { useState } from "react";
import { View } from "react-native";

export default function Cart() {
  const router = useRouter();
  const palette = usePalette();
  const { selected } = useBranches();
  const { track } = useOrderAlerts();
  const cart = useCart();
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!cart.branch || cart.lines.length === 0) {
    return (
      <View className="flex-1 items-center justify-center gap-4 bg-background p-6">
        <Ionicons name="cart-outline" size={72} color={palette.mutedForeground} />
        <Text className="text-xl font-semibold">Tu carrito está vacío</Text>
        <Text className="text-center text-muted-foreground">Agrega productos del menú y aparecerán aquí.</Text>
        {selected ? (
          <Button onPress={() => router.push(`/branch/${selected.id}`)}>
            <Text>Ordena ahora</Text>
          </Button>
        ) : null}
      </View>
    );
  }

  async function placeOrder() {
    if (!cart.branch) return;
    setError(null);
    setBusy(true);
    try {
      const order = await api<Order>("/api/orders/", {
        method: "POST",
        body: {
          branch: cart.branch.id,
          notes: notes.trim(),
          payment_method: "counter",
          items: cart.lines.map((l) => ({
            product: l.product.id,
            quantity: l.quantity,
            options: l.options.map((o) => o.id),
            notes: l.notes,
          })),
        },
      });
      cart.clear();
      setNotes("");
      track(order.id); // desde ya se le avisa de cada cambio, aunque salga de la pantalla de seguimiento
      router.push(`/order/${order.id}`);
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  }

  return (
    <KeyboardScrollView
      className="flex-1 bg-background"
      contentContainerClassName="items-center px-4 pt-14"
      bottomPadding={32}
      scrollToEndOnKeyboard
    >
      <View className="w-full max-w-md gap-4">
        <View className="gap-1">
          <Text className="text-3xl font-bold">Tu pedido</Text>
          <Text className="text-muted-foreground">Sucursal {cart.branch.name}</Text>
        </View>

        {cart.lines.map((line) => (
          <Card key={line.key}>
            <CardContent className="gap-3 pt-6">
              <View className="flex-row gap-3">
                <ProductThumb product={line.product} size={56} />
                <View className="flex-1 gap-1">
                  <Text className="font-semibold">{line.product.name}</Text>
                  {line.options.length > 0 ? (
                    <Text className="text-sm text-muted-foreground">{line.options.map((o) => o.name).join(" · ")}</Text>
                  ) : null}
                  {line.notes ? <Text className="text-sm italic text-muted-foreground">“{line.notes}”</Text> : null}
                </View>
                <Text className="font-semibold">{money(line.unitPrice * line.quantity)}</Text>
              </View>
              <View className="flex-row items-center justify-end gap-3">
                <Button size="icon" variant="outline" onPress={() => cart.changeQuantity(line.key, -1)} accessibilityLabel={line.quantity === 1 ? "Quitar del pedido" : "Quitar uno"}>
                  <Text>{line.quantity === 1 ? "×" : "−"}</Text>
                </Button>
                <Text className="w-6 text-center font-semibold">{line.quantity}</Text>
                <Button size="icon" variant="outline" onPress={() => cart.changeQuantity(line.key, 1)} accessibilityLabel="Agregar uno">
                  <Text>+</Text>
                </Button>
              </View>
            </CardContent>
          </Card>
        ))}

        <View className="gap-2">
          <Label nativeID="notes">Comentarios generales del pedido (opcional)</Label>
          <Input
            aria-labelledby="notes"
            value={notes}
            onChangeText={setNotes}
            maxLength={500}
            multiline
            placeholder="Pasaré en 10 minutos..."
          />
        </View>

        <View className="gap-2">
          <Text className="text-lg font-semibold">Forma de pago</Text>
          <View className="flex-row items-center gap-3 rounded-xl border border-primary bg-card p-3">
            <Ionicons name="radio-button-on" size={24} color={palette.primary} />
            <View className="flex-1">
              <Text className="font-medium">Pagar en el mostrador</Text>
              <Text className="text-sm text-muted-foreground">Efectivo o tarjeta al recoger tu pedido</Text>
            </View>
            <Ionicons name="storefront-outline" size={22} color={palette.mutedForeground} />
          </View>
          <View className="flex-row items-center gap-3 rounded-xl border border-border bg-card p-3 opacity-60">
            <Ionicons name="radio-button-off" size={24} color={palette.mutedForeground} />
            <View className="flex-1">
              <Text className="font-medium">Tarjeta en la app</Text>
              <Text className="text-sm text-muted-foreground">Paga desde tu celular y recoge sin pasar por caja</Text>
            </View>
            <Badge variant="outline">
              <Text>Pronto</Text>
            </Badge>
          </View>
        </View>

        <View className="flex-row items-center justify-between pt-2">
          <Text className="text-lg font-semibold">Total</Text>
          <Text className="text-lg font-semibold">{money(cart.total)}</Text>
        </View>

        {error ? <Text className="text-destructive">{error}</Text> : null}
        <Button size="lg" onPress={placeOrder} disabled={busy}>
          <Text>{busy ? "Enviando..." : `Hacer pedido · ${money(cart.total)}`}</Text>
        </Button>
      </View>
    </KeyboardScrollView>
  );
}
