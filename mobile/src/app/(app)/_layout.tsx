import { useAuth } from "@/lib/auth";
import { useBrand } from "@/lib/brand-provider";
import { useCart } from "@/lib/cart";
import { Link, Stack } from "expo-router";
import { Pressable, Text, View } from "react-native";

export default function AppLayout() {
  const brand = useBrand();
  const { logout } = useAuth();
  const { clear } = useCart();
  const link = { color: brand.primary_color, fontWeight: "600" as const };

  return (
    <Stack>
      <Stack.Screen
        name="index"
        options={{
          title: brand.name,
          headerRight: () => (
            <View style={{ flexDirection: "row", gap: 16 }}>
              <Link href="/orders" style={link}>
                Mis pedidos
              </Link>
              <Pressable
                onPress={() => {
                  clear();
                  logout();
                }}
                accessibilityRole="button"
                hitSlop={8}
              >
                <Text style={link}>Salir</Text>
              </Pressable>
            </View>
          ),
        }}
      />
      <Stack.Screen name="branch/[id]" options={{ title: "Menú" }} />
      <Stack.Screen name="cart" options={{ title: "Tu pedido" }} />
      <Stack.Screen name="order/[id]" options={{ title: "Seguimiento" }} />
      <Stack.Screen name="orders" options={{ title: "Mis pedidos" }} />
    </Stack>
  );
}
