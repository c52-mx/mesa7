import { useState, type ComponentProps } from "react";
import { Pressable, View } from "react-native";

import { Input } from "./ui/input";
import { Text } from "./ui/text";

/** Campo de contraseña con botón para mostrarla u ocultarla. */
export function PasswordInput(props: ComponentProps<typeof Input>) {
  const [visible, setVisible] = useState(false);
  return (
    <View className="justify-center">
      <Input {...props} secureTextEntry={!visible} autoCapitalize="none" autoCorrect={false} className="pr-20" />
      <Pressable
        onPress={() => setVisible((v) => !v)}
        accessibilityRole="button"
        accessibilityLabel={visible ? "Ocultar contraseña" : "Mostrar contraseña"}
        hitSlop={8}
        className="absolute right-3"
      >
        <Text className="text-sm font-medium text-muted-foreground">{visible ? "Ocultar" : "Mostrar"}</Text>
      </Pressable>
    </View>
  );
}
