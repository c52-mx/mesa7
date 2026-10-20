import { useBrand } from "@/lib/brand-provider";
import { ActivityIndicator, Image, View } from "react-native";

import { Text } from "./ui/text";

/** Pantalla de arranque con el logo y el nombre del negocio, mientras carga la sesión y la marca. */
export function BrandSplash() {
  const brand = useBrand();
  return (
    <View className="flex-1 items-center justify-center gap-5 bg-background">
      {brand.logo_url ? (
        <Image source={{ uri: brand.logo_url }} className="h-36 w-36 rounded-full" resizeMode="cover" />
      ) : null}
      <Text className="text-3xl font-bold">{brand.name}</Text>
      <ActivityIndicator />
    </View>
  );
}
