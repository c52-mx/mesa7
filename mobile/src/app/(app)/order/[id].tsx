import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Text } from "@/components/ui/text";
import type { Order } from "@/lib/api";
import { money, timeOf } from "@/lib/format";
import { watchOrder } from "@/lib/live";
import { STATUS_LABEL, STATUS_SHORT, STATUS_STEPS } from "@/lib/status";
import { useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, View } from "react-native";

export default function OrderTracking() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [order, setOrder] = useState<Order | null>(null);

  useEffect(() => watchOrder(Number(id), setOrder), [id]);

  if (!order) {
    return (
      <View className="flex-1 items-center justify-center bg-background">
        <ActivityIndicator />
      </View>
    );
  }

  const inKitchen = order.status === "received" || order.status === "preparing";
  const currentStep = STATUS_STEPS.indexOf(order.status);

  return (
    <ScrollView className="flex-1 bg-background" contentContainerClassName="items-center p-4">
      <View className="w-full max-w-md gap-4">
        <View className="items-center gap-2 py-4">
          <Text className="text-sm text-muted-foreground">Pedido #{order.id}</Text>
          <Text className="text-center text-3xl font-bold">{STATUS_LABEL[order.status]}</Text>
          {inKitchen ? (
            <Text className="text-muted-foreground">Listo aprox. a las {timeOf(order.estimated_ready_at)}</Text>
          ) : null}
        </View>

        {order.status === "cancelled" ? (
          <Badge variant="destructive" className="self-center">
            <Text>Este pedido fue cancelado</Text>
          </Badge>
        ) : (
          <View className="flex-row gap-2">
            {STATUS_STEPS.map((step, index) => (
              <View key={step} className="flex-1 gap-1">
                <View className={index <= currentStep ? "h-2 rounded-full bg-primary" : "h-2 rounded-full bg-muted"} />
                <Text className={index <= currentStep ? "text-xs font-medium" : "text-xs text-muted-foreground"}>
                  {STATUS_SHORT[step]}
                </Text>
              </View>
            ))}
          </View>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Tu pedido</CardTitle>
          </CardHeader>
          <CardContent className="gap-2">
            {order.items.map((item) => (
              <View key={item.product} className="flex-row justify-between">
                <Text>
                  {item.quantity} × {item.name}
                </Text>
                <Text>{money(Number(item.unit_price) * item.quantity)}</Text>
              </View>
            ))}
            <View className="mt-2 flex-row justify-between border-t border-border pt-2">
              <Text className="font-semibold">Total</Text>
              <Text className="font-semibold">{money(order.total)}</Text>
            </View>
            {order.notes ? <Text className="text-sm text-muted-foreground">Notas: {order.notes}</Text> : null}
          </CardContent>
        </Card>
      </View>
    </ScrollView>
  );
}
