import { api, getAccessToken, type Order } from "./api";
import { API_URL, TENANT_SLUG } from "./config";

const POLL_MS = 15000;
const RETRY_MS = 3000;
const CLOSE_UNAUTHENTICATED = 4401;
const CLOSE_FORBIDDEN = 4403;

/**
 * Sigue un pedido en vivo: entrega el estado actual y cada cambio.
 * Usa WebSocket y, como respaldo, consulta cada 15 s por si el socket se cae.
 * Devuelve la función para dejar de seguirlo.
 */
export function watchOrder(orderId: number, onOrder: (order: Order) => void): () => void {
  let stopped = false;
  let socket: WebSocket | null = null;
  let retry: ReturnType<typeof setTimeout> | undefined;

  const fetchOrder = async () => {
    try {
      const order = await api<Order>(`/api/orders/${orderId}/`);
      if (!stopped) onOrder(order);
    } catch {
      // sin conexión: el siguiente intento lo reintenta
    }
  };

  const connect = async () => {
    // El GET renueva el access token si hace falta y da el estado actual antes de abrir el socket.
    await fetchOrder();
    const token = getAccessToken();
    if (stopped || !token) return;
    socket = new WebSocket(`${API_URL.replace(/^http/, "ws")}/ws/orders/${orderId}/`);
    socket.onopen = () => socket?.send(JSON.stringify({ type: "auth", token, tenant: TENANT_SLUG }));
    socket.onmessage = (event) => {
      const message = JSON.parse(String(event.data));
      if (message.type === "order.update" && !stopped) onOrder(message.order);
    };
    socket.onclose = (event) => {
      if (stopped || event.code === CLOSE_UNAUTHENTICATED || event.code === CLOSE_FORBIDDEN) return;
      retry = setTimeout(connect, RETRY_MS);
    };
  };

  connect();
  const poll = setInterval(fetchOrder, POLL_MS);

  return () => {
    stopped = true;
    clearInterval(poll);
    if (retry) clearTimeout(retry);
    socket?.close();
  };
}
