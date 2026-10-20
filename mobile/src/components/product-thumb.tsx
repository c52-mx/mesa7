import type { Product } from "@/lib/api";
import { usePalette } from "@/lib/brand-provider";
import Ionicons from "@expo/vector-icons/Ionicons";
import { Image, View } from "react-native";

/** Foto del producto; si no tiene, un cuadro con los colores de la marca. */
export function ProductThumb({ product, size, className }: { product: Product; size?: number; className?: string }) {
  const palette = usePalette();
  const style = size ? { width: size, height: size } : undefined;
  if (product.image_url) {
    return <Image source={{ uri: product.image_url }} style={style} className={`rounded-xl bg-muted ${className ?? ""}`} resizeMode="cover" />;
  }
  return (
    <View style={style} className={`items-center justify-center rounded-xl bg-accent ${className ?? ""}`}>
      <Ionicons name="cafe-outline" size={size ? size * 0.4 : 32} color={palette.primary} />
    </View>
  );
}
