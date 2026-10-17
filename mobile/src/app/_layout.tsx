import "../../global.css";

import { AuthProvider, useAuth } from "@/lib/auth";
import { BrandProvider } from "@/lib/brand-provider";
import { Stack } from "expo-router";

function RootNavigator() {
  const { session, loading } = useAuth();
  if (loading) return null;

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
        <RootNavigator />
      </AuthProvider>
    </BrandProvider>
  );
}
