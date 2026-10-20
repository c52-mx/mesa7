import { BranchProvider } from "@/lib/branch";
import { Stack } from "expo-router";

export default function AppLayout() {
  return (
    <BranchProvider>
      <Stack>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="branch/[id]" options={{ title: "Menú" }} />
        <Stack.Screen name="cart" options={{ title: "Tu pedido" }} />
        <Stack.Screen name="order/[id]" options={{ title: "Seguimiento" }} />
      </Stack>
    </BranchProvider>
  );
}
