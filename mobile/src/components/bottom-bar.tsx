import { useKeyboardHeight } from "@/lib/keyboard";
import type { ReactNode } from "react";
import { View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

/**
 * Barra fija al pie de la pantalla (carrito, "Agregar"). Respeta la zona segura para que no la
 * tapen los botones de navegación del teléfono, y sube sobre el teclado cuando está abierto.
 * Dentro de las pestañas el inset ya lo cubre la barra de pestañas: ahí se usa `inset={false}`.
 */
export function BottomBar({ children, inset = true }: { children: ReactNode; inset?: boolean }) {
  const insets = useSafeAreaInsets();
  const keyboard = useKeyboardHeight();
  return (
    <View
      className="absolute left-0 right-0 items-center border-t border-border bg-background px-4 pt-4"
      style={{ bottom: keyboard, paddingBottom: (inset && keyboard === 0 ? insets.bottom : 0) + 16 }}
    >
      <View className="w-full max-w-md gap-3">{children}</View>
    </View>
  );
}
