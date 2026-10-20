import { ProgressBar } from "@/components/progress-bar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Text } from "@/components/ui/text";
import type { Loyalty } from "@/lib/api";
import { useBrand, usePalette } from "@/lib/brand-provider";
import { formatMemberCode, rewardProgress } from "@/lib/loyalty";
import { useApi } from "@/lib/use-api";
import Ionicons from "@expo/vector-icons/Ionicons";
import QRCode from "react-native-qrcode-svg";
import { ActivityIndicator, Image, ScrollView, View } from "react-native";

const KIND_LABEL = { earn: "Compra", redeem: "Canje", adjust: "Ajuste" } as const;

export default function LoyaltyCard() {
  const brand = useBrand();
  const palette = usePalette();
  const { data: loyalty, error, loading, reload } = useApi<Loyalty>("/api/loyalty/");

  if (loading) {
    return (
      <View className="flex-1 items-center justify-center bg-background">
        <ActivityIndicator />
      </View>
    );
  }
  if (error || !loyalty) {
    return (
      <View className="flex-1 items-center justify-center gap-4 bg-background p-6">
        <Text className="text-center text-muted-foreground">{error ?? "La tarjeta no está disponible."}</Text>
        <Button onPress={reload}>
          <Text>Reintentar</Text>
        </Button>
      </View>
    );
  }

  const perPoint = Number(loyalty.spend_per_point);

  return (
    <ScrollView className="flex-1 bg-background" contentContainerClassName="items-center px-4 pb-8 pt-14">
      <View className="w-full max-w-md gap-5">
        <Text className="text-3xl font-bold">Mi tarjeta</Text>

        {/* Tarjeta con los colores de la marca */}
        <View className="gap-8 rounded-3xl bg-secondary p-6">
          <View className="flex-row items-center gap-3">
            {brand.logo_url ? <Image source={{ uri: brand.logo_url }} className="h-10 w-10" resizeMode="contain" /> : null}
            <Text className="text-xl font-bold text-secondary-foreground">{brand.name}</Text>
          </View>
          <View className="flex-row items-end justify-between gap-4">
            <View className="flex-1 gap-1">
              <Text className="text-lg font-semibold tracking-widest text-secondary-foreground">
                {formatMemberCode(loyalty.member_code)}
              </Text>
              <Text className="text-secondary-foreground">{loyalty.name}</Text>
            </View>
            <View className="rounded-lg bg-white p-2">
              <QRCode value={loyalty.qr} size={88} color="#000000" backgroundColor="#FFFFFF" />
            </View>
          </View>
        </View>
        <Text className="text-center text-sm text-muted-foreground">Muestra este código en caja para sumar tus puntos.</Text>

        <Card>
          <CardContent className="gap-3 pt-6">
            <View className="flex-row items-end gap-2">
              <Text className="text-5xl font-bold">{loyalty.points}</Text>
              <Text className="pb-2 text-muted-foreground">puntos</Text>
            </View>
            <ProgressBar value={rewardProgress(loyalty)} />
            <Text className="text-sm text-muted-foreground">
              {loyalty.next_reward
                ? `Te faltan ${loyalty.next_reward.missing} puntos para: ${loyalty.next_reward.name}`
                : "¡Desbloqueaste todas las recompensas!"}
            </Text>
          </CardContent>
        </Card>

        {loyalty.rewards.length > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>Recompensas</CardTitle>
            </CardHeader>
            <CardContent className="gap-3">
              {loyalty.rewards.map((reward) => (
                <View key={reward.id} className="flex-row items-center gap-3">
                  <Ionicons
                    name={reward.unlocked ? "checkmark-circle" : "ellipse-outline"}
                    size={24}
                    color={reward.unlocked ? palette.primary : palette.mutedForeground}
                  />
                  <Text className={reward.unlocked ? "flex-1 font-medium" : "flex-1 text-muted-foreground"}>
                    {reward.name}
                  </Text>
                  <Text className="text-sm text-muted-foreground">{reward.points_required} pts</Text>
                </View>
              ))}
              <Text className="text-sm text-muted-foreground">Pide el canje en caja cuando desbloquees una recompensa.</Text>
            </CardContent>
          </Card>
        ) : null}

        <Card>
          <CardHeader>
            <CardTitle>Cómo ganar puntos</CardTitle>
          </CardHeader>
          <CardContent>
            <Text className="text-muted-foreground">
              Ganas 1 punto por cada ${perPoint} de compra. Los puntos se suman cuando recoges tu pedido.
            </Text>
          </CardContent>
        </Card>

        {loyalty.recent.length > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>Movimientos</CardTitle>
            </CardHeader>
            <CardContent className="gap-3">
              {loyalty.recent.map((movement, index) => (
                <View key={index} className="flex-row items-center justify-between">
                  <View>
                    <Text className="font-medium">{movement.note || KIND_LABEL[movement.kind]}</Text>
                    <Text className="text-sm text-muted-foreground">
                      {new Date(movement.created_at).toLocaleDateString("es-MX")}
                    </Text>
                  </View>
                  <Text className="font-semibold">
                    {movement.points > 0 ? "+" : ""}
                    {movement.points}
                  </Text>
                </View>
              ))}
            </CardContent>
          </Card>
        ) : null}
      </View>
    </ScrollView>
  );
}
