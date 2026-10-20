import { useEffect, useState } from "react";

import type { KdsOrder, OrderStatus } from "./api";

export const ACTIVE_STATUSES: OrderStatus[] = ["received", "preparing", "ready"];

/** Siguiente paso del flujo normal y el texto del botón que lo ejecuta. */
export const NEXT_STEP: Partial<Record<OrderStatus, { status: OrderStatus; label: string }>> = {
  received: { status: "preparing", label: "Preparar" },
  preparing: { status: "ready", label: "Listo" },
  ready: { status: "delivered", label: "Entregado" },
};

export const SEMAPHORE_COLOR = { green: "#16a34a", yellow: "#ca8a04", red: "#dc2626" } as const;
export type Semaphore = keyof typeof SEMAPHORE_COLOR;

export function elapsedMinutes(order: KdsOrder, now: number): number {
  return Math.max(0, Math.floor((now - Date.parse(order.created_at)) / 60000));
}

/** Mismo criterio que el servidor: verde hasta el tiempo estimado, amarillo hasta +50 %, rojo después. */
export function semaphoreOf(order: KdsOrder, now: number): Semaphore {
  if (order.status === "ready") return "green";
  const ratio = (now - Date.parse(order.created_at)) / 60000 / Math.max(order.prep_minutes, 1);
  return ratio <= 1 ? "green" : ratio <= 1.5 ? "yellow" : "red";
}

/** Hora actual que se refresca cada `ms` para que los cronómetros avancen solos. */
export function useNow(ms = 30000): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), ms);
    return () => clearInterval(timer);
  }, [ms]);
  return now;
}

export function byCreation(a: KdsOrder, b: KdsOrder): number {
  return Date.parse(a.created_at) - Date.parse(b.created_at);
}
