import { useBrand } from "@/lib/brand-provider";
import { Image } from "react-native";

/** Logo del negocio (si lo configuró). Sin logo no ocupa espacio. */
export function BrandLogo({ size = 48 }: { size?: number }) {
  const brand = useBrand();
  if (!brand.logo_url) return null;
  return (
    <Image
      source={{ uri: brand.logo_url }}
      style={{ width: size, height: size }}
      className="rounded-full"
      resizeMode="cover"
      accessibilityLabel={`Logo de ${brand.name}`}
    />
  );
}
