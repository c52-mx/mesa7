import { api, getAccessToken, type KdsOrder, type Order } from "./api";
import { API_URL, TENANT_SLUG } from "./config";

const POLL_MS = 15000;
const RETRY_MS = 3000;
const CLOSE_UNAUTHENTICATED = 4401;
const CLOSE_FORBIDDEN = 4403;

/**
 * Mantiene una conexión en vivo: carga el estado (`refresh`), abre el WebSocket autenticado y
 * entrega cada mensaje. Como respaldo vuelve a cargar cada 15 s por si el socket se cae.
 * Devuelve la función para cerrar todo.
 */
function watchSocket(path: string, refresh: () => Promise<void>, onMessage: (message: any) => void): () => void {
  let stopped = false;
  let socket: WebSocket | null = null;
  let retry: ReturnType<typeof setTimeout> | undefined;

  const safeRefresh = async () => {
    try {
      await refresh();
    } catch {
      // sin conexión: el siguiente intento lo reintenta
    }
  };

  const connect = async () => {
    // La carga renueva el access token si hace falta y da el estado actual antes de abrir el socket.
    await safeRefresh();
    const token = getAccessToken();
    if (stopped || !token) return;
    socket = new WebSocket(`${API_URL.replace(/^http/, "ws")}${path}`);
    socket.onopen = () => socket?.send(JSON.stringify({ type: "auth", token, tenant: TENANT_SLUG }));
    socket.onmessage = (event) => {
      if (!stopped) onMessage(JSON.parse(String(event.data)));
    };
    socket.onclose = (event) => {
      if (stopped || event.code === CLOSE_UNAUTHENTICATED || event.code === CLOSE_FORBIDDEN) return;
      retry = setTimeout(connect, RETRY_MS);
    };
  };

  connect();
  const poll = setInterval(safeRefresh, POLL_MS);

  return () => {
    stopped = true;
    clearInterval(poll);
    if (retry) clearTimeout(retry);
    socket?.close();
  };
}

/** Sigue un pedido en vivo (cliente): entrega el estado actual y cada cambio. */
export function watchOrder(orderId: number, onOrder: (order: Order) => void): () => void {
  let stopped = false;
  const refresh = async () => {
    const order = await api<Order>(`/api/orders/${orderId}/`);
    if (!stopped) onOrder(order);
  };
  const stop = watchSocket(`/ws/orders/${orderId}/`, refresh, (message) => {
    if (message.type === "order.update") onOrder(message.order);
  });
  return () => {
    stopped = true;
    stop();
  };
}

/**
 * Pedidos activos de una sucursal en vivo (personal).
 * `onSnapshot` recibe la lista completa; `onUpdate` cada pedido nuevo o que cambió.
 */
export function watchKds(
  branchId: number,
  onSnapshot: (orders: KdsOrder[]) => void,
  onUpdate: (order: KdsOrder) => void,
): () => void {
  let stopped = false;
  const refresh = async () => {
    const orders = await api<KdsOrder[]>(`/api/kds/orders/?branch=${branchId}`);
    if (!stopped) onSnapshot(orders);
  };
  const stop = watchSocket(`/ws/kds/${branchId}/`, refresh, (message) => {
    if (message.type === "order.update") onUpdate(message.order);
  });
  return () => {
    stopped = true;
    stop();
  };
}
