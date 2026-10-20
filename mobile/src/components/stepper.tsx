import { View } from "react-native";

import { Button } from "./ui/button";
import { Text } from "./ui/text";

type Props = { quantity: number; onAdd: () => void; onRemove: () => void };

/** "Agregar" cuando no hay unidades; con unidades, − cantidad +. */
export function Stepper({ quantity, onAdd, onRemove }: Props) {
  if (quantity === 0) {
    return (
      <Button size="sm" onPress={onAdd}>
        <Text>Agregar</Text>
      </Button>
    );
  }
  return (
    <View className="flex-row items-center gap-3">
      <Button size="icon" variant="outline" onPress={onRemove} accessibilityLabel="Quitar uno">
        <Text>−</Text>
      </Button>
      <Text className="w-6 text-center font-semibold">{quantity}</Text>
      <Button size="icon" onPress={onAdd} accessibilityLabel="Agregar uno">
        <Text>+</Text>
      </Button>
    </View>
  );
}
