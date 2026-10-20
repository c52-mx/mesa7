import { useKeyboardHeight } from "@/lib/keyboard";
import { useEffect, useRef } from "react";
import { ScrollView, type ScrollViewProps } from "react-native";

type Props = ScrollViewProps & {
  /** Espacio inferior base (por ejemplo la zona segura); se le suma la altura del teclado. */
  bottomPadding?: number;
  /** Al abrir el teclado baja hasta el final: para pantallas cuyo campo de texto es lo último. */
  scrollToEndOnKeyboard?: boolean;
};

/** ScrollView que no deja el contenido tapado por el teclado. */
export function KeyboardScrollView({
  bottomPadding = 0,
  scrollToEndOnKeyboard = false,
  contentContainerStyle,
  children,
  ...rest
}: Props) {
  const ref = useRef<ScrollView>(null);
  const keyboard = useKeyboardHeight();

  useEffect(() => {
    if (keyboard === 0 || !scrollToEndOnKeyboard) return;
    // Espera a que el espacio extra ya esté dibujado antes de bajar.
    const timer = setTimeout(() => ref.current?.scrollToEnd({ animated: true }), 150);
    return () => clearTimeout(timer);
  }, [keyboard, scrollToEndOnKeyboard]);

  return (
    <ScrollView
      ref={ref}
      keyboardShouldPersistTaps="handled"
      contentContainerStyle={[contentContainerStyle, { paddingBottom: bottomPadding + keyboard }]}
      {...rest}
    >
      {children}
    </ScrollView>
  );
}
