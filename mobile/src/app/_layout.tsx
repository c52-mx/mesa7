import "../../global.css";

import { NAV_THEME } from "@/lib/theme";
import { PortalHost } from "@rn-primitives/portal";
import { Stack } from "expo-router";
import { ThemeProvider } from "expo-router/react-navigation";
import { StatusBar } from "expo-status-bar";
import { useColorScheme } from "nativewind";

export default function RootLayout() {
  const { colorScheme } = useColorScheme();
  const scheme = colorScheme === "dark" ? "dark" : "light";

  return (
    <ThemeProvider value={NAV_THEME[scheme]}>
      <StatusBar style={scheme === "dark" ? "light" : "dark"} />
      <Stack />
      <PortalHost />
    </ThemeProvider>
  );
}
