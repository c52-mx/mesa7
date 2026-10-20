import { API_URL, TENANT_SLUG } from "./config";

export type Tokens = { access: string; refresh: string };
export type Membership = { tenant: string; name: string; role: string };
export type Branding = {
  slug: string;
  name: string;
  primary_color: string;
  secondary_color: string;
  logo_url: string;
  loyalty_enabled: boolean;
};
export type Banner = { id: number; title: string; text: string; image_url: string };
export type Me = { email: string; full_name: string; phone: string };
export type LoyaltyReward = { id: number; name: string; points_required: number; unlocked: boolean };
export type Loyalty = {
  name: string;
  member_code: string;
  qr: string;
  points: number;
  spend_per_point: string;
  rewards: LoyaltyReward[];
  next_reward: (LoyaltyReward & { missing: number }) | null;
  recent: { points: number; kind: "earn" | "redeem" | "adjust"; note: string; created_at: string }[];
};
export type Branch = { id: number; name: string; address: string };
export type Option = { id: number; name: string; price_delta: string; is_popular: boolean };
export type OptionGroup = {
  id: number;
  name: string;
  /** Mínimo a elegir: 0 = opcional. */
  required: number;
  max_select: number;
  options: Option[];
};
export type Product = {
  id: number;
  name: string;
  description: string;
  price: string;
  image_url: string;
  /** Ilustración de la categoría (cafe, cold, food, dessert, burger, drink, fruit). */
  icon: string;
  is_featured: boolean;
  prep_time_minutes: number;
  option_groups: OptionGroup[];
};
/** Opción elegida, tal como la guarda el pedido. */
export type OrderOption = { group: string; name: string; price_delta: string };
export type MenuCategory = { id: number; name: string; products: Product[] };
export type Menu = { branch: { id: number; name: string }; categories: MenuCategory[] };

export type OrderStatus = "received" | "preparing" | "ready" | "delivered" | "cancelled";
export type Order = {
  id: number;
  status: OrderStatus;
  branch: number;
  total: string;
  notes: string;
  payment_method: "counter" | "online";
  payment_status: "pending" | "paid";
  created_at: string;
  status_changed_at: string;
  estimated_ready_at: string;
  items: {
    product: number;
    name: string;
    quantity: number;
    unit_price: string;
    options: OrderOption[];
    notes: string;
  }[];
};

export class ApiError extends Error {
  constructor(
    public status: number,
    public data: unknown,
  ) {
    super(`API ${status}`);
  }
}

// Sesión actual: la fija AuthProvider; el cliente renueva el access token solo.
let tokens: Tokens | null = null;
let onTokens: (t: Tokens | null) => void = () => {};

export function setSession(next: Tokens | null, listener?: (t: Tokens | null) => void) {
  tokens = next;
  if (listener) onTokens = listener;
}

/** Access token vigente (para el handshake del WebSocket). */
export const getAccessToken = () => tokens?.access ?? null;

type Options = { method?: string; body?: unknown; auth?: boolean };

async function send(path: string, { method = "GET", body, auth = true }: Options) {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (auth && tokens) {
    headers.Authorization = `Bearer ${tokens.access}`;
    headers["X-Tenant"] = TENANT_SLUG;
  }
  return fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

async function refreshAccess(): Promise<boolean> {
  if (!tokens) return false;
  const response = await send("/api/auth/token/refresh/", {
    method: "POST",
    body: { refresh: tokens.refresh },
    auth: false,
  });
  if (!response.ok) return false;
  const data = (await response.json()) as { access: string; refresh?: string };
  tokens = { access: data.access, refresh: data.refresh ?? tokens.refresh };
  onTokens(tokens);
  return true;
}

export async function api<T>(path: string, options: Options = {}): Promise<T> {
  let response = await send(path, options);
  if (response.status === 401 && options.auth !== false && (await refreshAccess())) {
    response = await send(path, options);
  }
  if (response.status === 401 && options.auth !== false) {
    tokens = null;
    onTokens(null);
  }
  const text = await response.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    // Respuesta que no es JSON (por ejemplo un 500 con HTML): se trata como error sin detalle.
  }
  if (!response.ok) throw new ApiError(response.status, data);
  return data as T;
}

/** Texto para mostrar al usuario a partir de cualquier error. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 429) return "Demasiados intentos. Espera un minuto e inténtalo de nuevo.";
    if (error.status === 401) return "Correo o contraseña incorrectos.";
    const data = error.data;
    if (data && typeof data === "object") {
      const messages = Object.values(data as Record<string, unknown>).flat().filter(
        (m): m is string => typeof m === "string",
      );
      if (messages.length) return messages.join(" ");
    }
    return "Ocurrió un error. Inténtalo de nuevo.";
  }
  return "No se pudo conectar con el servidor. Revisa tu conexión.";
}
