import { AuthScreen } from "@/components/auth-screen";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Text } from "@/components/ui/text";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Link } from "expo-router";
import { useState } from "react";
import { View } from "react-native";

export default function Register() {
  const { register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setError(null);
    setBusy(true);
    try {
      await register({ email, password, full_name: fullName.trim(), phone: phone.trim() });
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  }

  return (
    <AuthScreen title="Crea tu cuenta">
      <View className="gap-4">
        <View className="gap-2">
          <Label nativeID="name">Nombre</Label>
          <Input aria-labelledby="name" value={fullName} onChangeText={setFullName} autoComplete="name" />
        </View>
        <View className="gap-2">
          <Label nativeID="email">Correo</Label>
          <Input
            aria-labelledby="email"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            autoComplete="email"
            keyboardType="email-address"
            placeholder="tu@correo.com"
          />
        </View>
        <View className="gap-2">
          <Label nativeID="phone">Teléfono (opcional)</Label>
          <Input
            aria-labelledby="phone"
            value={phone}
            onChangeText={setPhone}
            autoComplete="tel"
            keyboardType="phone-pad"
          />
        </View>
        <View className="gap-2">
          <Label nativeID="password">Contraseña</Label>
          <Input
            aria-labelledby="password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            autoComplete="new-password"
            onSubmitEditing={submit}
          />
          <Text className="text-sm text-muted-foreground">Mínimo 8 caracteres, no solo números.</Text>
        </View>
        {error ? <Text className="text-destructive">{error}</Text> : null}
        <Button onPress={submit} disabled={busy || !email || !password}>
          <Text>{busy ? "Creando cuenta..." : "Crear cuenta"}</Text>
        </Button>
        <Link href="/login" asChild>
          <Button variant="ghost">
            <Text>¿Ya tienes cuenta? Inicia sesión</Text>
          </Button>
        </Link>
      </View>
    </AuthScreen>
  );
}
