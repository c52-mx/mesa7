import { AuthScreen } from "@/components/auth-screen";
import { PasswordInput } from "@/components/password-input";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Text } from "@/components/ui/text";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Link } from "expo-router";
import { useState } from "react";
import { View } from "react-native";

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  }

  return (
    <AuthScreen title="Inicia sesión">
      <View className="gap-4">
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
          <Label nativeID="password">Contraseña</Label>
          <PasswordInput
            aria-labelledby="password"
            value={password}
            onChangeText={setPassword}
            autoComplete="password"
            onSubmitEditing={submit}
          />
        </View>
        {error ? <Text className="text-destructive">{error}</Text> : null}
        <Button onPress={submit} disabled={busy || !email || !password}>
          <Text>{busy ? "Entrando..." : "Entrar"}</Text>
        </Button>
        <Link href="/register" asChild>
          <Button variant="ghost">
            <Text>¿No tienes cuenta? Regístrate</Text>
          </Button>
        </Link>
      </View>
    </AuthScreen>
  );
}
