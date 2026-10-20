import type { OrderStatus } from "./api";

export const STATUS_LABEL: Record<OrderStatus, string> = {
  received: "Recibido",
  preparing: "Preparando",
  ready: "¡Listo para recoger!",
  delivered: "Entregado",
  cancelled: "Cancelado",
};

/** Etiqueta corta para barras de progreso e insignias. */
export const STATUS_SHORT: Record<OrderStatus, string> = {
  received: "Recibido",
  preparing: "Preparando",
  ready: "Listo",
  delivered: "Entregado",
  cancelled: "Cancelado",
};

/** Pasos del seguimiento, en orden. */
export const STATUS_STEPS: OrderStatus[] = ["received", "preparing", "ready", "delivered"];
