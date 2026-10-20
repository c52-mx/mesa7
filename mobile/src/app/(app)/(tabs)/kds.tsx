import { BranchPicker } from "@/components/branch-picker";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Text } from "@/components/ui/text";
import { api, errorMessage, type KdsOrder, type OrderStatus } from "@/lib/api";
import { useBranches } from "@/lib/branch";
import { money } from "@/lib/format";
import {
  ACTIVE_STATUSES,
  NEXT_STEP,
  SEMAPHORE_COLOR,
  byCreation,
  elapsedMinutes,
  semaphoreOf,
  useNow,
} from "@/lib/kds";
import { watchKds } from "@/lib/live";
import { STATUS_SHORT } from "@/lib/status";
import { useEffect, useRef, useState } from "react";
import { ActivityIndicator, Alert, ScrollView, Vibration, View } from "react-native";

export default function Kds() {
  const { selected } = useBranches();
  const now = useNow();
  const [orders, setOrders] = useState<KdsOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<number | null>(null);
  const known = useRef(new Set<number>());

  useEffect(() => {
    if (!selected) return;
    setOrders([]);
    setLoading(true);
    known.current = new Set();
    let first = true;
    return watchKds(
      selected.id,
      (list) => {
        list.forEach((o) => known.current.add(o.id));
        setOrders([...list].sort(byCreation));
        setLoading(false);
        first = false;
      },
      (order) => {
        const active = ACTIVE_STATUSES.includes(order.status);
        const isNew = !known.current.has(order.id);
        known.current.add(order.id);
        if (isNew && active && !first) Vibration.vibrate([0, 300, 150, 300]); // pedido nuevo
        setOrders((current) => {
          const rest = current.filter((o) => o.id !== order.id);
          return active ? [...rest, order].sort(byCreation) : rest;
        });
      },
    );
  }, [selected?.id]);

  function replace(updated: KdsOrder) {
    setOrders((current) => {
      const rest = current.filter((o) => o.id !== updated.id);
      return ACTIVE_STATUSES.includes(updated.status) ? [...rest, updated].sort(byCreation) : rest;
    });
  }

  async function call(order: KdsOrder, path: string, body?: unknown) {
    setBusy(order.id);
    try {
      replace(await api<KdsOrder>(`/api/kds/orders/${order.id}/${path}/`, { method: "POST", body }));
    } catch (e) {
      Alert.alert("No se pudo actualizar el pedido", errorMessage(e));
    } finally {
      setBusy(null);
    }
  }

  const setStatus = (order: KdsOrder, status: OrderStatus) => call(order, "status", { status });

  function confirmCancel(order: KdsOrder) {
    Alert.alert(`Cancelar pedido #${order.id}`, "El cliente recibirá el aviso de cancelación.", [
      { text: "Volver", style: "cancel" },
      { text: "Cancelar pedido", style: "destructive", onPress: () => setStatus(order, "cancelled") },
    ]);
  }

  return (
    <ScrollView className="flex-1 bg-background" contentContainerClassName="items-center px-4 pb-8 pt-14">
      <View className="w-full max-w-2xl gap-4">
        <View className="flex-row items-end justify-between gap-3">
          <View className="gap-1">
            <Text className="text-3xl font-bold">Pedidos</Text>
            <Text className="text-muted-foreground">
              {loading ? "Cargando..." : `${orders.length} activo${orders.length === 1 ? "" : "s"}`}
            </Text>
          </View>
          <BranchPicker />
        </View>

        {loading ? <ActivityIndicator className="py-8" /> : null}
        {!loading && orders.length === 0 ? (
          <Text className="py-12 text-center text-muted-foreground">No hay pedidos activos. Aquí aparecerán en cuanto lleguen.</Text>
        ) : null}

        {orders.map((order) => {
          const color = SEMAPHORE_COLOR[semaphoreOf(order, now)];
          const next = NEXT_STEP[order.status];
          return (
            <Card key={order.id} style={{ borderLeftWidth: 6, borderLeftColor: color }}>
              <CardContent className="gap-3 pt-6">
                <View className="flex-row items-start justify-between gap-3">
                  <View className="flex-1">
                    <Text className="text-lg font-bold">
                      #{order.id} · {order.customer}
                    </Text>
                    <Text className="text-sm text-muted-foreground">{STATUS_SHORT[order.status]}</Text>
                  </View>
                  <View className="items-end">
                    <Text className="text-2xl font-bold" style={{ color }}>
                      {elapsedMinutes(order, now)} min
                    </Text>
                    <Text className="text-xs text-muted-foreground">de ~{order.prep_minutes} min</Text>
                  </View>
                </View>

                <View className="gap-2 border-t border-border pt-3">
                  {order.items.map((item, index) => (
                    <View key={index}>
                      <Text className="font-semibold">
                        {item.quantity} × {item.name}
                      </Text>
                      {item.options.length > 0 ? (
                        <Text className="text-sm text-muted-foreground">{item.options.map((o) => o.name).join(" · ")}</Text>
                      ) : null}
                      {item.notes ? <Text className="text-sm font-medium text-destructive">“{item.notes}”</Text> : null}
                    </View>
                  ))}
                  {order.notes ? <Text className="text-sm font-medium text-destructive">Pedido: {order.notes}</Text> : null}
                </View>

                <View className="flex-row items-center justify-between gap-3 border-t border-border pt-3">
                  {order.payment_status === "paid" ? (
                    <Badge variant="secondary">
                      <Text>Pagado</Text>
                    </Badge>
                  ) : (
                    <Button size="sm" variant="outline" disabled={busy === order.id} onPress={() => call(order, "paid")}>
                      <Text>Cobrar {money(order.total)}</Text>
                    </Button>
                  )}
                  <View className="flex-row gap-2">
                    <Button size="sm" variant="ghost" disabled={busy === order.id} onPress={() => confirmCancel(order)}>
                      <Text>Cancelar</Text>
                    </Button>
                    {next ? (
                      <Button size="sm" disabled={busy === order.id} onPress={() => setStatus(order, next.status)}>
                        <Text>{next.label}</Text>
                      </Button>
                    ) : null}
                  </View>
                </View>
              </CardContent>
            </Card>
          );
        })}
      </View>
    </ScrollView>
  );
}
