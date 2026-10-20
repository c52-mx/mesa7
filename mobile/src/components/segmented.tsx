import { Pressable, View } from "react-native";

import { Text } from "./ui/text";

type Props<T extends string> = {
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
};

/** Pestañas internas de una pantalla (por ejemplo Ordena | Historial). */
export function Segmented<T extends string>({ options, value, onChange }: Props<T>) {
  return (
    <View className="flex-row rounded-full bg-muted p-1">
      {options.map((option) => {
        const active = option.value === value;
        return (
          <Pressable
            key={option.value}
            onPress={() => onChange(option.value)}
            accessibilityRole="tab"
            accessibilityState={{ selected: active }}
            className={active ? "flex-1 items-center rounded-full bg-background py-2 shadow-sm" : "flex-1 items-center py-2"}
          >
            <Text className={active ? "font-semibold" : "text-muted-foreground"}>{option.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}
