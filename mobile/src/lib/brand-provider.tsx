import { PortalHost } from "@rn-primitives/portal";
import { DarkTheme, DefaultTheme, ThemeProvider, type Theme } from "expo-router/react-navigation";
import { StatusBar } from "expo-status-bar";
import { useColorScheme, vars } from "nativewind";
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { View } from "react-native";

import { api, type Branding } from "./api";
import { brandPalette, isHex, paletteVars } from "./brand";
import { TENANT_SLUG } from "./config";
import { storage } from "./storage";

const CACHE_KEY = "branding";

// Mientras llega la marca del servidor (o si falla) se usa un tema neutro.
const FALLBACK: Branding = {
  slug: TENANT_SLUG,
  name: "Mesa7",
  primary_color: "#171717",
  secondary_color: "#F5F5F5",
  logo_url: "",
};

const BrandContext = createContext<Branding>(FALLBACK);
export const useBrand = () => useContext(BrandContext);

export function BrandProvider({ children }: { children: ReactNode }) {
  const [branding, setBranding] = useState<Branding>(FALLBACK);
  const { colorScheme } = useColorScheme();
  const mode = colorScheme === "dark" ? "dark" : "light";

  useEffect(() => {
    let alive = true;
    // Última marca conocida al instante, y luego la del servidor.
    storage
      .get(CACHE_KEY)
      .then((cached) => cached && alive && setBranding(JSON.parse(cached)))
      .catch(() => {});
    api<Branding>(`/api/tenants/${TENANT_SLUG}/`, { auth: false })
      .then((fresh) => {
        if (!alive || !isHex(fresh.primary_color) || !isHex(fresh.secondary_color)) return;
        setBranding(fresh);
        storage.set(CACHE_KEY, JSON.stringify(fresh)).catch(() => {});
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);

  const palette = useMemo(() => {
    const ok = isHex(branding.primary_color) && isHex(branding.secondary_color);
    return brandPalette(
      ok ? branding.primary_color : FALLBACK.primary_color,
      ok ? branding.secondary_color : FALLBACK.secondary_color,
      mode,
    );
  }, [branding, mode]);

  const navTheme: Theme = useMemo(
    () => ({
      ...(mode === "dark" ? DarkTheme : DefaultTheme),
      colors: {
        background: palette.background,
        border: palette.border,
        card: palette.card,
        notification: palette.destructive,
        primary: palette.primary,
        text: palette.foreground,
      },
    }),
    [palette, mode],
  );

  return (
    <BrandContext.Provider value={branding}>
      <ThemeProvider value={navTheme}>
        <StatusBar style={mode === "dark" ? "light" : "dark"} />
        {/* Las variables CSS van en la raíz; PortalHost va dentro para que los diálogos las hereden. */}
        <View style={[{ flex: 1 }, vars(paletteVars(palette))]}>
          {children}
          <PortalHost />
        </View>
      </ThemeProvider>
    </BrandContext.Provider>
  );
}
