import { usePathname, useRouter } from "expo-router";
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Animated, Pressable, Vibration, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { Text } from "@/components/ui/text";

import { api, type Order, type OrderStatus } from "./api";
import { useBrand } from "./brand-provider";
import { watchOrder } from "./live";

const ACTIVE: OrderStatus[] = ["received", "preparing", "ready"];
const MAX_WATCHED = 5;
const SHOW_MS = 7000;

// Qué se le dice al cliente cuando su pedido cambia de estado.
const MESSAGES: Partial<Record<OrderStatus, (id: number) => string>> = {
  preparing: (id) => `Tu pedido #${id} está en preparación`,
  ready: (id) => `¡Tu pedido #${id} está listo! Pasa a recogerlo`,
  delivered: (id) => `Gracias por tu pedido #${id}`,
  cancelled: (id) => `Tu pedido #${id} fue cancelado`,
};

type Alert = { key: number; orderId: number; message: string };

const AlertsContext = createContext<{ track: (orderId: number) => void }>({ track: () => {} });
export const useOrderAlerts = () => useContext(AlertsContext);

/**
 * Sigue los pedidos activos del cliente y le avisa con un banner cuando cambian de estado,
 * en cualquier pantalla. Solo funciona con la app abierta; con la app cerrada hace falta push.
 */
export function OrderAlertsProvider({ children }: { children: ReactNode }) {
  const [alert, setAlert] = useState<Alert | null>(null);
  const watchers = useRef(new Map<number, () => void>());
  const statuses = useRef(new Map<number, OrderStatus>());
  const pathname = usePathname();
  const pathRef = useRef(pathname);
  pathRef.current = pathname;

  const stop = useCallback((orderId: number) => {
    watchers.current.get(orderId)?.();
    watchers.current.delete(orderId);
  }, []);

  const track = useCallback(
    (orderId: number) => {
      if (watchers.current.has(orderId)) return;
      const unwatch = watchOrder(orderId, (order) => {
        const previous = statuses.current.get(order.id);
        statuses.current.set(order.id, order.status);
        const message = MESSAGES[order.status]?.(order.id);
        // La primera lectura solo fija el estado inicial; y no se avisa si ya está viendo ese pedido.
        if (previous && previous !== order.status && message && !pathRef.current.endsWith(`/order/${order.id}`)) {
          setAlert({ key: Date.now(), orderId: order.id, message });
          Vibration.vibrate([0, 250, 120, 250]);
        }
        if (!ACTIVE.includes(order.status)) stop(order.id);
      });
      watchers.current.set(orderId, unwatch);
    },
    [stop],
  );

  useEffect(() => {
    const active = watchers.current;
    api<Order[]>("/api/orders/")
      .then((orders) => orders.filter((o) => ACTIVE.includes(o.status)).slice(0, MAX_WATCHED).forEach((o) => track(o.id)))
      .catch(() => {});
    return () => {
      active.forEach((unwatch) => unwatch());
      active.clear();
    };
  }, [track]);

  const dismiss = useCallback(() => setAlert(null), []);
  const value = useMemo(() => ({ track }), [track]);
  return (
    <AlertsContext.Provider value={value}>
      {children}
      {alert ? <AlertBanner key={alert.key} alert={alert} onDone={dismiss} /> : null}
    </AlertsContext.Provider>
  );
}

function AlertBanner({ alert, onDone }: { alert: Alert; onDone: () => void }) {
  const insets = useSafeAreaInsets();
  const brand = useBrand();
  const router = useRouter();
  const slide = useRef(new Animated.Value(-140)).current;

  useEffect(() => {
    Animated.timing(slide, { toValue: 0, duration: 250, useNativeDriver: true }).start();
    const timer = setTimeout(onDone, SHOW_MS);
    return () => clearTimeout(timer);
  }, [slide, onDone]);

  return (
    <Animated.View
      style={{ transform: [{ translateY: slide }], top: insets.top + 8 }}
      className="absolute left-0 right-0 items-center px-4"
      pointerEvents="box-none"
    >
      <View className="w-full max-w-md">
        <Pressable
          onPress={() => {
            onDone();
            router.push(`/order/${alert.orderId}`);
          }}
          accessibilityRole="alert"
          accessibilityLabel={alert.message}
          className="gap-1 rounded-2xl border border-border bg-card p-4"
        >
          <Text className="text-xs font-semibold uppercase tracking-widest text-primary">{brand.name}</Text>
          <Text className="text-base font-semibold">{alert.message}</Text>
          <Text className="text-sm text-muted-foreground">Toca para ver el seguimiento</Text>
        </Pressable>
      </View>
    </Animated.View>
  );
}
