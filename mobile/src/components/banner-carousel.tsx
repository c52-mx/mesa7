import type { Banner } from "@/lib/api";
import { useState } from "react";
import { ImageBackground, ScrollView, View, useWindowDimensions } from "react-native";

import { Text } from "./ui/text";

const GAP = 12;

/** Carrusel de promociones. Sin imagen, la tarjeta usa el color principal de la marca. */
export function BannerCarousel({ banners }: { banners: Banner[] }) {
  const { width } = useWindowDimensions();
  const [page, setPage] = useState(0);
  const slideWidth = Math.min(width - 32, 420);

  if (banners.length === 0) return null;
  return (
    <View className="gap-3">
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        snapToInterval={slideWidth + GAP}
        decelerationRate="fast"
        contentContainerStyle={{ gap: GAP }}
        onMomentumScrollEnd={(e) => setPage(Math.round(e.nativeEvent.contentOffset.x / (slideWidth + GAP)))}
      >
        {banners.map((banner) => (
          <View key={banner.id} style={{ width: slideWidth }} className="h-40 overflow-hidden rounded-2xl bg-primary">
            <ImageBackground source={banner.image_url ? { uri: banner.image_url } : undefined} className="h-full justify-end">
              <View className={banner.image_url ? "gap-1 bg-black/45 p-4" : "gap-1 p-4"}>
                <Text className={banner.image_url ? "text-xl font-bold text-white" : "text-xl font-bold text-primary-foreground"}>
                  {banner.title}
                </Text>
                {banner.text ? (
                  <Text className={banner.image_url ? "text-white" : "text-primary-foreground"}>{banner.text}</Text>
                ) : null}
              </View>
            </ImageBackground>
          </View>
        ))}
      </ScrollView>
      {banners.length > 1 ? (
        <View className="flex-row justify-center gap-1.5">
          {banners.map((banner, index) => (
            <View
              key={banner.id}
              className={index === page ? "h-2 w-5 rounded-full bg-primary" : "h-2 w-2 rounded-full bg-muted"}
            />
          ))}
        </View>
      ) : null}
    </View>
  );
}
