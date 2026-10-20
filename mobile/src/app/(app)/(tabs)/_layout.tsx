import { useBrand, usePalette } from "@/lib/brand-provider";
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

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: palette.primary,
        tabBarInactiveTintColor: palette.mutedForeground,
        tabBarStyle: { backgroundColor: palette.card, borderTopColor: palette.border },
      }}
    >
      <Tabs.Screen name="index" options={{ title: "Inicio", tabBarIcon: icon("home", "home-outline") }} />
      <Tabs.Screen name="order" options={{ title: "Ordena", tabBarIcon: icon("cafe", "cafe-outline") }} />
      {/* Si el negocio apaga la lealtad, la pestaña desaparece. */}
      <Tabs.Screen
        name="card"
        options={{
          title: "Mi tarjeta",
          tabBarIcon: icon("qr-code", "qr-code-outline"),
          href: brand.loyalty_enabled ? undefined : null,
        }}
      />
      <Tabs.Screen name="profile" options={{ title: "Perfil", tabBarIcon: icon("person", "person-outline") }} />
    </Tabs>
  );
}
