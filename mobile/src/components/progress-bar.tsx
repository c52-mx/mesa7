import { View } from "react-native";

/** `value` entre 0 y 1. */
export function ProgressBar({ value }: { value: number }) {
  const percent = Math.round(Math.min(1, Math.max(0, value)) * 100);
  return (
    <View
      className="h-2.5 overflow-hidden rounded-full bg-muted"
      accessibilityRole="progressbar"
      accessibilityValue={{ min: 0, max: 100, now: percent }}
    >
      <View className="h-full rounded-full bg-primary" style={{ width: `${percent}%` }} />
    </View>
  );
}
