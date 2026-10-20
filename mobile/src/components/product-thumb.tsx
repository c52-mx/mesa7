import type { Product } from "@/lib/api";
import { usePalette } from "@/lib/brand-provider";
import Ionicons from "@expo/vector-icons/Ionicons";
import type { ComponentProps } from "react";
import { Image, View } from "react-native";

type IconName = ComponentProps<typeof Ionicons>["name"];

// Mismos valores que Category.icon en el backend.
const ICONS: Record<string, IconName> = {
  cafe: "cafe-outline",
  cold: "snow-outline",
  food: "restaurant-outline",
  dessert: "ice-cream-outline",
  burger: "fast-food-outline",
  drink: "wine-outline",
  fruit: "nutrition-outline",
};

/** Foto del producto; si no tiene, una ilustración de su categoría con los colores de la marca. */
export function ProductThumb({ product, size, className }: { product: Product; size?: number; className?: string }) {
  const palette = usePalette();
  const style = size ? { width: size, height: size } : undefined;
  if (product.image_url) {
    return <Image source={{ uri: product.image_url }} style={style} className={`rounded-xl bg-muted ${className ?? ""}`} resizeMode="cover" />;
  }
  return (
    <View style={style} className={`items-center justify-center rounded-xl bg-accent ${className ?? ""}`}>
      <Ionicons name={ICONS[product.icon] ?? "cafe-outline"} size={size ? size * 0.4 : 40} color={palette.primary} />
    </View>
  );
}
