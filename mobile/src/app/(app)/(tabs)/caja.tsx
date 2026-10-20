import { KeyboardScrollView } from "@/components/keyboard-scroll-view";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Text } from "@/components/ui/text";
import { api, errorMessage, type CustomerCard } from "@/lib/api";
import { usePalette } from "@/lib/brand-provider";
import { formatMemberCode } from "@/lib/loyalty";
import Ionicons from "@expo/vector-icons/Ionicons";
import { CameraView, useCameraPermissions } from "expo-camera";
import { useRef, useState } from "react";
import { Alert, View } from "react-native";

const enc = encodeURIComponent;

export default function Caja() {
  const palette = usePalette();
  const [permission, requestPermission] = useCameraPermissions();
  const [card, setCard] = useState<CustomerCard | null>(null);
  const [manual, setManual] = useState("");
  const [amount, setAmount] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(null);
  const scanLock = useRef(false); // el lector dispara varias veces por el mismo QR

  async function lookup(raw: string) {
    setBusy(true);
    setMessage(null);
    try {
      setCard(await api<CustomerCard>(`/api/staff/loyalty/lookup/?code=${enc(raw)}`));
      setAmount("");
    } catch (e) {
      setMessage({ text: errorMessage(e), ok: false });
      // Pausa corta: si no, el lector volvería a leer el mismo QR en cada cuadro.
      setTimeout(() => (scanLock.current = false), 2000);
    } finally {
      setBusy(false);
    }
  }

  /** Devuelve true si el servidor aceptó la operación. */
  async function act(path: string, body: Record<string, unknown>, success: string): Promise<boolean> {
    if (!card) return false;
    setBusy(true);
    try {
      setCard(await api<CustomerCard>(`/api/staff/loyalty/${path}/`, { method: "POST", body: { code: card.member_code, ...body } }));
      setMessage({ text: success, ok: true });
      return true;
    } catch (e) {
      setMessage({ text: errorMessage(e), ok: false });
      return false;
    } finally {
      setBusy(false);
    }
  }

  function confirmRedeem(reward: CustomerCard["rewards"][number]) {
    Alert.alert("Canjear recompensa", `${reward.name}\nSe descontarán ${reward.points_required} puntos.`, [
      { text: "Cancelar", style: "cancel" },
      { text: "Canjear", onPress: () => act("redeem", { reward: reward.id }, `Canje registrado: ${reward.name}.`) },
    ]);
  }

  function reset() {
    setCard(null);
    setManual("");
    setMessage(null);
    scanLock.current = false;
  }

  const perPoint = card ? Number(card.spend_per_point) : 0;
  const parsed = Number(amount.replace(",", "."));
  const preview = card && parsed > 0 && perPoint > 0 ? Math.floor(parsed / perPoint) : 0;

  return (
    <KeyboardScrollView className="flex-1 bg-background" contentContainerClassName="items-center px-4 pt-14" bottomPadding={32}>
      <View className="w-full max-w-md gap-5">
        <Text className="text-3xl font-bold">Caja</Text>

        {!card ? (
          <>
            {permission?.granted ? (
              <View className="gap-2">
                <View className="h-72 overflow-hidden rounded-2xl bg-muted">
                  <CameraView
                    style={{ flex: 1 }}
                    facing="back"
                    barcodeScannerSettings={{ barcodeTypes: ["qr"] }}
                    onBarcodeScanned={({ data }) => {
                      if (scanLock.current || busy) return;
                      scanLock.current = true;
                      lookup(data);
                    }}
                  />
                </View>
                <Text className="text-center text-sm text-muted-foreground">Apunta al QR de la tarjeta del cliente.</Text>
              </View>
            ) : (
              <Card>
                <CardContent className="items-center gap-3 pt-6">
                  <Ionicons name="qr-code-outline" size={48} color={palette.mutedForeground} />
                  <Text className="text-center text-muted-foreground">
                    {permission && !permission.canAskAgain
                      ? "El permiso de la cámara está bloqueado. Actívalo en los ajustes del teléfono o escribe el código."
                      : "Para escanear el QR de la tarjeta necesitamos acceso a la cámara."}
                  </Text>
                  {permission?.canAskAgain !== false ? (
                    <Button onPress={requestPermission}>
                      <Text>Permitir cámara</Text>
                    </Button>
                  ) : null}
                </CardContent>
              </Card>
            )}

            <View className="gap-2">
              <Label nativeID="code">O escribe el código de la tarjeta</Label>
              <Input
                aria-labelledby="code"
                value={manual}
                onChangeText={setManual}
                keyboardType="number-pad"
                placeholder="1234 5678 9012"
                onSubmitEditing={() => manual.trim() && lookup(manual)}
              />
              <Button variant="outline" disabled={busy || !manual.trim()} onPress={() => lookup(manual)}>
                <Text>Buscar tarjeta</Text>
              </Button>
            </View>
          </>
        ) : (
          <>
            <Card>
              <CardContent className="gap-1 pt-6">
                <Text className="text-xl font-bold">{card.customer}</Text>
                <Text className="text-muted-foreground">Tarjeta {formatMemberCode(card.member_code)}</Text>
                <View className="flex-row items-end gap-2 pt-2">
                  <Text className="text-5xl font-bold">{card.points}</Text>
                  <Text className="pb-2 text-muted-foreground">puntos</Text>
                </View>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recompensas</CardTitle>
              </CardHeader>
              <CardContent className="gap-3">
                {card.rewards.length === 0 ? <Text className="text-muted-foreground">Este negocio no tiene recompensas.</Text> : null}
                {card.rewards.map((reward) => (
                  <View key={reward.id} className="flex-row items-center justify-between gap-3">
                    <View className="flex-1">
                      <Text className={reward.unlocked ? "font-medium" : "text-muted-foreground"}>{reward.name}</Text>
                      <Text className="text-sm text-muted-foreground">{reward.points_required} pts</Text>
                    </View>
                    <Button size="sm" variant={reward.unlocked ? "default" : "outline"} disabled={!reward.unlocked || busy} onPress={() => confirmRedeem(reward)}>
                      <Text>{reward.unlocked ? "Canjear" : "Faltan " + (reward.points_required - card.points)}</Text>
                    </Button>
                  </View>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Compra en mostrador</CardTitle>
              </CardHeader>
              <CardContent className="gap-3">
                <Label nativeID="amount">Monto de la compra ($)</Label>
                <Input aria-labelledby="amount" value={amount} onChangeText={setAmount} keyboardType="decimal-pad" placeholder="0.00" />
                <Text className="text-sm text-muted-foreground">
                  {preview > 0 ? `Sumará ${preview} punto${preview === 1 ? "" : "s"}` : `1 punto por cada $${perPoint}`}
                </Text>
                <Button
                  disabled={busy || preview <= 0}
                  onPress={async () => {
                    if (await act("earn", { amount: amount.replace(",", ".") }, `Se sumaron ${preview} puntos.`)) setAmount("");
                  }}
                >
                  <Text>Sumar puntos</Text>
                </Button>
              </CardContent>
            </Card>
          </>
        )}

        {message ? (
          <View className="flex-row items-center gap-2">
            <Ionicons name={message.ok ? "checkmark-circle" : "alert-circle"} size={20} color={message.ok ? palette.primary : "#dc2626"} />
            <Text className={message.ok ? "flex-1 font-medium" : "flex-1 text-destructive"}>{message.text}</Text>
          </View>
        ) : null}

        {card ? (
          <Button variant="outline" onPress={reset}>
            <Text>Escanear otra tarjeta</Text>
          </Button>
        ) : null}
      </View>
    </KeyboardScrollView>
  );
}
