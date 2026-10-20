import { BranchProvider } from "@/lib/branch";
import { OrderAlertsProvider } from "@/lib/order-alerts";
import { Stack } from "expo-router";

export default function AppLayout() {
  return (
    <BranchProvider>
      <OrderAlertsProvider>
        <Stack>
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen name="branch/[id]" options={{ title: "Menú" }} />
          <Stack.Screen name="product/[id]" options={{ title: "Personaliza tu pedido" }} />
          <Stack.Screen name="order/[id]" options={{ title: "Seguimiento" }} />
        </Stack>
      </OrderAlertsProvider>
    </BranchProvider>
  );
}
