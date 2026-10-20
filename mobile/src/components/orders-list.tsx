import type { Order } from "@/lib/api";
import { money } from "@/lib/format";
import { STATUS_SHORT } from "@/lib/status";
import { useApi } from "@/lib/use-api";
import { Link } from "expo-router";
import { ActivityIndicator, Pressable, View } from "react-native";

import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Text } from "./ui/text";

/** Historial de pedidos del cliente. */
export function OrdersList() {
  const { data: orders, error, reload } = useApi<Order[]>("/api/orders/");

  if (error) {
    return (
      <View className="items-center gap-4 py-8">
        <Text className="text-center text-destructive">{error}</Text>
        <Button onPress={reload}>
          <Text>Reintentar</Text>
        </Button>
      </View>
    );
  }
  if (!orders) return <ActivityIndicator className="py-8" />;
  if (orders.length === 0) return <Text className="py-8 text-center text-muted-foreground">Aún no has hecho pedidos.</Text>;

  return (
    <View className="gap-3">
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
  );
}
