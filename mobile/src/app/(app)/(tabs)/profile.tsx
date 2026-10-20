import { KeyboardScrollView } from "@/components/keyboard-scroll-view";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Text } from "@/components/ui/text";
import { api, errorMessage, type Me } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useCart } from "@/lib/cart";
import { useApi } from "@/lib/use-api";
import { useEffect, useState } from "react";
import { ActivityIndicator, View } from "react-native";

export default function Profile() {
  const { logout } = useAuth();
  const cart = useCart();
  const { data: me, error, loading, reload } = useApi<Me>("/api/me/");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(null);

  useEffect(() => {
    if (me) {
      setFullName(me.full_name);
      setPhone(me.phone);
    }
  }, [me]);

  async function save() {
    setSaving(true);
    setMessage(null);
    try {
      await api<Me>("/api/me/", { method: "PATCH", body: { full_name: fullName, phone } });
      setMessage({ text: "Datos guardados.", ok: true });
    } catch (e) {
      setMessage({ text: errorMessage(e), ok: false });
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <View className="flex-1 items-center justify-center bg-background">
        <ActivityIndicator />
      </View>
    );
  }
  if (error || !me) {
    return (
      <View className="flex-1 items-center justify-center gap-4 bg-background p-6">
        <Text className="text-center text-destructive">{error}</Text>
        <Button onPress={reload}>
          <Text>Reintentar</Text>
        </Button>
      </View>
    );
  }

  const initial = (me.full_name || me.email).charAt(0).toUpperCase();

  return (
    <KeyboardScrollView className="flex-1 bg-background" contentContainerClassName="items-center px-4 pt-14" bottomPadding={32}>
      <View className="w-full max-w-md gap-5">
        <Text className="text-3xl font-bold">Perfil</Text>

        <View className="items-center gap-2 py-2">
          <View className="h-20 w-20 items-center justify-center rounded-full bg-primary">
            <Text className="text-3xl font-bold text-primary-foreground">{initial}</Text>
          </View>
          <Text className="text-muted-foreground">{me.email}</Text>
        </View>

        <Card>
          <CardContent className="gap-4 pt-6">
            <View className="gap-2">
              <Label nativeID="full_name">Nombre</Label>
              <Input aria-labelledby="full_name" value={fullName} onChangeText={setFullName} autoComplete="name" />
            </View>
            <View className="gap-2">
              <Label nativeID="phone">Teléfono</Label>
              <Input
                aria-labelledby="phone"
                value={phone}
                onChangeText={setPhone}
                keyboardType="phone-pad"
                autoComplete="tel"
              />
            </View>
            {message ? (
              <Text className={message.ok ? "text-muted-foreground" : "text-destructive"}>{message.text}</Text>
            ) : null}
            <Button onPress={save} disabled={saving}>
              <Text>{saving ? "Guardando..." : "Guardar cambios"}</Text>
            </Button>
          </CardContent>
        </Card>

        <Button
          variant="outline"
          onPress={() => {
            cart.clear();
            logout();
          }}
        >
          <Text>Cerrar sesión</Text>
        </Button>
      </View>
    </KeyboardScrollView>
  );
}
