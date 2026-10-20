import "../../global.css";

import { AuthProvider, useAuth } from "@/lib/auth";
import { BrandSplash } from "@/components/brand-splash";
import { BrandProvider, useBrandReady } from "@/lib/brand-provider";
import { CartProvider } from "@/lib/cart";
import { Stack } from "expo-router";

function RootNavigator() {
  const { session, loading } = useAuth();
  const brandReady = useBrandReady();
  if (loading || !brandReady) return <BrandSplash />;

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Protected guard={!!session}>
        <Stack.Screen name="(app)" />
      </Stack.Protected>
      <Stack.Protected guard={!session}>
        <Stack.Screen name="(auth)" />
      </Stack.Protected>
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <BrandProvider>
      <AuthProvider>
        <CartProvider>
          <RootNavigator />
        </CartProvider>
      </AuthProvider>
    </BrandProvider>
  );
}
