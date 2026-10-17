import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Text } from "@/components/ui/text";
import { api, errorMessage, type Branch } from "@/lib/api";
import { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, View } from "react-native";

export default function Branches() {
  const [branches, setBranches] = useState<Branch[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setBranches(null);
    try {
      setBranches(await api<Branch[]>("/api/branches/"));
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (error) {
    return (
      <View className="flex-1 items-center justify-center gap-4 bg-background p-6">
        <Text className="text-center text-destructive">{error}</Text>
        <Button onPress={load}>
          <Text>Reintentar</Text>
        </Button>
      </View>
    );
  }

  if (!branches) {
    return (
      <View className="flex-1 items-center justify-center bg-background">
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <ScrollView className="flex-1 bg-background" contentContainerClassName="gap-4 p-4">
      <Text className="text-xl font-semibold">Elige tu sucursal</Text>
      {branches.length === 0 ? (
        <Text className="text-muted-foreground">Este negocio aún no tiene sucursales activas.</Text>
      ) : (
        branches.map((branch) => (
          <Card key={branch.id}>
            <CardHeader>
              <CardTitle>{branch.name}</CardTitle>
              {branch.address ? <CardDescription>{branch.address}</CardDescription> : null}
            </CardHeader>
            <CardContent>
              <Button disabled>
                <Text>Ver menú (próximamente)</Text>
              </Button>
            </CardContent>
          </Card>
        ))
      )}
    </ScrollView>
  );
}
