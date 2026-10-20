import { Stepper } from "@/components/stepper";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Text } from "@/components/ui/text";
import { api, errorMessage, type Order } from "@/lib/api";
import { useCart } from "@/lib/cart";
import { money } from "@/lib/format";
import { useRouter } from "expo-router";
import { useState } from "react";
import { ScrollView, View } from "react-native";

export default function Cart() {
  const router = useRouter();
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
          items: cart.lines.map((l) => ({ product: l.product.id, quantity: l.quantity })),
        },
      });
      cart.clear();
      router.replace(`/order/${order.id}`);
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  }

  return (
    <ScrollView className="flex-1 bg-background" contentContainerClassName="items-center p-4">
      <View className="w-full max-w-md gap-4">
        <Text className="text-xl font-semibold">{cart.branch.name}</Text>

        {cart.lines.map((line) => (
          <Card key={line.product.id}>
            <CardContent className="flex-row items-center justify-between gap-3 pt-6">
              <View className="flex-1 gap-1">
                <Text className="font-semibold">{line.product.name}</Text>
                <Text className="text-sm text-muted-foreground">
                  {money(line.product.price)} × {line.quantity} = {money(Number(line.product.price) * line.quantity)}
                </Text>
              </View>
              <Stepper
                quantity={line.quantity}
                onAdd={() => cart.add(cart.branch!, line.product)}
                onRemove={() => cart.remove(line.product.id)}
              />
            </CardContent>
          </Card>
        ))}

        <View className="gap-2">
          <Label nativeID="notes">Notas para la cocina (opcional)</Label>
          <Input
            aria-labelledby="notes"
            value={notes}
            onChangeText={setNotes}
            maxLength={500}
            multiline
            placeholder="Sin azúcar, leche deslactosada..."
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
