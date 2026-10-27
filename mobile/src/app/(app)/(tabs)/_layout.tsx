import { useAuth } from "@/lib/auth";
import { useBrand, usePalette } from "@/lib/brand-provider";
import { useCart } from "@/lib/cart";
import Ionicons from "@expo/vector-icons/Ionicons";
import { Tabs } from "expo-router";
import type { ComponentProps } from "react";
import type { ColorValue } from "react-native";

type IconName = ComponentProps<typeof Ionicons>["name"];

const icon =
  (active: IconName, inactive: IconName) =>
  ({ focused, color, size }: { focused: boolean; color: ColorValue; size: number }) => (
    <Ionicons name={focused ? active : inactive} size={size} color={color} />
  );

export default function TabsLayout() {
  const brand = useBrand();
  const palette = usePalette();
  const cart = useCart();
  const { isStaff } = useAuth();

  // Las pestañas que no corresponden al rol se ocultan (href: null), no se eliminan.
  const customer = isStaff ? null : undefined;
  const ordering = !isStaff && brand.orders_enabled ? undefined : null;

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: palette.primary,
        tabBarInactiveTintColor: palette.mutedForeground,
        tabBarStyle: { backgroundColor: palette.card, borderTopColor: palette.border },
      }}
    >
      <Tabs.Screen name="index" options={{ title: "Inicio", tabBarIcon: icon("home", "home-outline"), href: customer }} />
      <Tabs.Screen name="order" options={{ title: "Ordena", tabBarIcon: icon("cafe", "cafe-outline"), href: ordering }} />
      {/* El contador está siempre a la vista, igual que en Uber Eats. */}
      <Tabs.Screen
        name="cart"
        options={{
          title: "Carrito",
          tabBarIcon: icon("cart", "cart-outline"),
          tabBarBadge: cart.count > 0 ? cart.count : undefined,
          tabBarBadgeStyle: { backgroundColor: palette.primary, color: palette.primaryForeground },
          href: ordering,
        }}
      />
      {/* Si el negocio apaga la lealtad, la pestaña desaparece. */}
      <Tabs.Screen
        name="card"
        options={{
          title: "Mi tarjeta",
          tabBarIcon: icon("qr-code", "qr-code-outline"),
          href: !isStaff && brand.loyalty_enabled ? undefined : null,
        }}
      />
      <Tabs.Screen name="kds" options={{ title: "Pedidos", tabBarIcon: icon("receipt", "receipt-outline"), href: isStaff && brand.kds_enabled ? undefined : null }} />
      <Tabs.Screen
        name="caja"
        options={{
          title: "Caja",
          tabBarIcon: icon("scan", "scan-outline"),
          href: isStaff && brand.loyalty_enabled ? undefined : null,
        }}
      />
      <Tabs.Screen name="profile" options={{ title: "Perfil", tabBarIcon: icon("person", "person-outline") }} />
    </Tabs>
  );
}
