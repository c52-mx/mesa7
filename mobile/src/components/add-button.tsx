import { usePalette } from "@/lib/brand-provider";
import Ionicons from "@expo/vector-icons/Ionicons";
import { Pressable } from "react-native";

import { Text } from "./ui/text";

/** Botón redondo "+": muestra la cantidad que ya hay en el carrito. */
export function AddButton({ quantity, onPress, label }: { quantity: number; onPress: () => void; label: string }) {
  const palette = usePalette();
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={label}
      hitSlop={6}
      className="h-9 w-9 items-center justify-center rounded-full bg-primary"
    >
      {quantity > 0 ? (
        <Text className="font-bold text-primary-foreground">{quantity}</Text>
      ) : (
        <Ionicons name="add" size={22} color={palette.primaryForeground} />
      )}
    </Pressable>
  );
}
