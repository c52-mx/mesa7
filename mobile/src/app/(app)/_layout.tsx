import { useAuth } from "@/lib/auth";
import { useBrand } from "@/lib/brand-provider";
import { Stack } from "expo-router";
import { Pressable, Text } from "react-native";

export default function AppLayout() {
  const brand = useBrand();
  const { logout } = useAuth();
  return (
    <Stack
      screenOptions={{
        headerRight: () => (
          <Pressable onPress={logout} accessibilityRole="button" hitSlop={8}>
            <Text style={{ color: brand.primary_color, fontWeight: "600" }}>Salir</Text>
          </Pressable>
        ),
      }}
    >
      <Stack.Screen name="index" options={{ title: brand.name }} />
    </Stack>
  );
}
