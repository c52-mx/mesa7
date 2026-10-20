import { ProductThumb } from "@/components/product-thumb";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Text } from "@/components/ui/text";
import { api, errorMessage, type Order } from "@/lib/api";
import { useCart } from "@/lib/cart";
import { money } from "@/lib/format";
import { useOrderAlerts } from "@/lib/order-alerts";
import { useRouter } from "expo-router";
import { useState } from "react";
import { ScrollView, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

export default function Cart() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { track } = useOrderAlerts();
  const cart = useCart();
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!cart.branch || cart.lines.length === 0) {
    return (
      <View className="flex-1 items-center justify-center gap-4 bg-background p-6">
        <Text className="text-muted-foreground">Tu pedido está vacío.</Text>
        <Button onPress={() => router.back()}>
          <Text>Volver al menú</Text>
        </Button>
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
          items: cart.lines.map((l) => ({
            product: l.product.id,
            quantity: l.quantity,
            options: l.options.map((o) => o.id),
            notes: l.notes,
          })),
        },
      });
      cart.clear();
      track(order.id); // desde ya se le avisa de cada cambio, aunque salga de la pantalla de seguimiento
      router.replace(`/order/${order.id}`);
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  }

  return (
    <ScrollView
      className="flex-1 bg-background"
      contentContainerClassName="items-center p-4"
      contentContainerStyle={{ paddingBottom: 32 + insets.bottom }}
    >
      <View className="w-full max-w-md gap-4">
        <Text className="text-xl font-semibold">{cart.branch.name}</Text>

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

        <View className="flex-row items-center justify-between">
          <Text className="text-lg font-semibold">Total</Text>
          <Text className="text-lg font-semibold">{money(cart.total)}</Text>
        </View>
        <Text className="text-sm text-muted-foreground">Pagas en el mostrador al recoger tu pedido.</Text>

        {error ? <Text className="text-destructive">{error}</Text> : null}
        <Button size="lg" onPress={placeOrder} disabled={busy}>
          <Text>{busy ? "Enviando..." : "Hacer pedido"}</Text>
        </Button>
      </View>
    </ScrollView>
  );
}
