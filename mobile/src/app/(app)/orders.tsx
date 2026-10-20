import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Text } from "@/components/ui/text";
import { api, errorMessage, type Order } from "@/lib/api";
import { money } from "@/lib/format";
import { STATUS_SHORT } from "@/lib/status";
import { Link, useFocusEffect } from "expo-router";
import { useCallback, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, View } from "react-native";

export default function Orders() {
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setOrders(await api<Order[]>("/api/orders/"));
    } catch (e) {
      setError(errorMessage(e));
    }
  }, []);

  // Recarga cada vez que se vuelve a esta pantalla (por ejemplo tras hacer un pedido).
  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

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
  if (!orders) {
    return (
      <View className="flex-1 items-center justify-center bg-background">
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <ScrollView className="flex-1 bg-background" contentContainerClassName="items-center p-4">
      <View className="w-full max-w-md gap-3">
        {orders.length === 0 ? (
          <Text className="text-muted-foreground">Aún no has hecho pedidos.</Text>
        ) : null}
        {orders.map((order) => (
          <Link key={order.id} href={`/order/${order.id}`} asChild>
            <Pressable accessibilityRole="button">
              <Card>
                <CardContent className="flex-row items-center justify-between pt-6">
                  <View className="gap-1">
                    <Text className="font-semibold">Pedido #{order.id}</Text>
                    <Text className="text-sm text-muted-foreground">
                      {new Date(order.created_at).toLocaleDateString("es-MX")} · {money(order.total)}
                    </Text>
                  </View>
                  <Badge variant={order.status === "cancelled" ? "destructive" : "secondary"}>
                    <Text>{STATUS_SHORT[order.status]}</Text>
                  </Badge>
                </CardContent>
              </Card>
            </Pressable>
          </Link>
        ))}
      </View>
    </ScrollView>
  );
}
