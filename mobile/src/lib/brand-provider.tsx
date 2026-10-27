import { PortalHost } from "@rn-primitives/portal";
import { DarkTheme, DefaultTheme, ThemeProvider, type Theme } from "expo-router/react-navigation";
import { StatusBar } from "expo-status-bar";
import { useColorScheme, vars } from "nativewind";
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { View } from "react-native";

import { api, type Branding } from "./api";
import { brandPalette, isHex, paletteVars, type Palette } from "./brand";
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
  loyalty_enabled: false,
  orders_enabled: true,
  kds_enabled: true,
};

const BrandContext = createContext<Branding>(FALLBACK);
export const useBrand = () => useContext(BrandContext);

/** false mientras se carga la marca por primera vez (para no mostrar un instante el tema neutro). */
const ReadyContext = createContext(false);
export const useBrandReady = () => useContext(ReadyContext);

// Si el servidor tarda, se sigue con lo que haya en vez de dejar la pantalla de carga.
const READY_TIMEOUT_MS = 2000;

// Paleta derivada del tenant (para íconos, barras y otros colores que no pasan por clases).
const PaletteContext = createContext<Palette>(brandPalette(FALLBACK.primary_color, FALLBACK.secondary_color, "light"));
export const usePalette = () => useContext(PaletteContext);

export function BrandProvider({ children }: { children: ReactNode }) {
  const [branding, setBranding] = useState<Branding>(FALLBACK);
  const [ready, setReady] = useState(false);
  const { colorScheme } = useColorScheme();
  const mode = colorScheme === "dark" ? "dark" : "light";

  useEffect(() => {
    let alive = true;
    const finish = () => alive && setReady(true);
    // Última marca conocida al instante, y luego la del servidor.
    storage
      .get(CACHE_KEY)
      .then((cached) => {
        if (cached && alive) {
          setBranding({ ...FALLBACK, ...JSON.parse(cached) }); // una marca guardada antes de los módulos no los trae
          finish();
        }
      })
      .catch(() => {});
    api<Branding>(`/api/tenants/${TENANT_SLUG}/`, { auth: false })
      .then((fresh) => {
        if (!alive || !isHex(fresh.primary_color) || !isHex(fresh.secondary_color)) return;
        setBranding(fresh);
        storage.set(CACHE_KEY, JSON.stringify(fresh)).catch(() => {});
      })
      .catch(() => {})
      .finally(finish);
    const timeout = setTimeout(finish, READY_TIMEOUT_MS);
    return () => {
      alive = false;
      clearTimeout(timeout);
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
      <ReadyContext.Provider value={ready}>
      <PaletteContext.Provider value={palette}>
        <ThemeProvider value={navTheme}>
          <StatusBar style={mode === "dark" ? "light" : "dark"} />
          {/* Las variables CSS van en la raíz; PortalHost va dentro para que los diálogos las hereden. */}
          <View style={[{ flex: 1 }, vars(paletteVars(palette))]}>
            {children}
            <PortalHost />
          </View>
        </ThemeProvider>
      </PaletteContext.Provider>
      </ReadyContext.Provider>
    </BrandContext.Provider>
  );
}
