import { useEffect, useState } from "react";
import { Keyboard } from "react-native";

/**
 * Altura actual del teclado (0 si está oculto).
 *
 * En Android con pantalla completa el teclado se dibuja encima de la app sin reducirla, así que las
 * pantallas con campos de texto suman esta altura a su espacio inferior para poder desplazarse.
 */
export function useKeyboardHeight(): number {
  const [height, setHeight] = useState(0);
  useEffect(() => {
    const show = Keyboard.addListener("keyboardDidShow", (e) => setHeight(e.endCoordinates.height));
    const hide = Keyboard.addListener("keyboardDidHide", () => setHeight(0));
    return () => {
      show.remove();
      hide.remove();
    };
  }, []);
  return height;
}
