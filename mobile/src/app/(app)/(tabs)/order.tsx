import { OrdersList } from "@/components/orders-list";
import { Segmented } from "@/components/segmented";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Text } from "@/components/ui/text";
import { useBranches } from "@/lib/branch";
import { Link } from "expo-router";
import { useState } from "react";
import { ActivityIndicator, Linking, Pressable, ScrollView, View } from "react-native";

export default function Order() {
  const { branches, selected, select, loading, error, reload } = useBranches();
  const [tab, setTab] = useState<"order" | "history">("order");

  return (
    <ScrollView className="flex-1 bg-background" contentContainerClassName="items-center px-4 pb-8 pt-14">
      <View className="w-full max-w-md gap-5">
        <Text className="text-3xl font-bold">Ordena</Text>
        <Segmented
          value={tab}
          onChange={setTab}
          options={[
            { value: "order", label: "Ordena" },
            { value: "history", label: "Historial" },
          ]}
        />

        {tab === "history" ? (
          <OrdersList />
        ) : (
          <View className="gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Pickup</CardTitle>
                <CardDescription>Ordena tus favoritos, evita filas y recógelos en tu sucursal.</CardDescription>
              </CardHeader>
              <CardContent className="gap-3">
                {selected ? (
                  <>
                    <View className="gap-1">
                      <Text className="font-medium">{selected.name}</Text>
                      {selected.address ? <Text className="text-sm text-muted-foreground">{selected.address}</Text> : null}
                      {selected.hours ? <Text className="text-sm text-muted-foreground">{selected.hours}</Text> : null}
                      {selected.phone ? (
                        <Pressable onPress={() => Linking.openURL(`tel:${selected.phone.replace(/\s/g, "")}`)} accessibilityRole="link">
                          <Text className="text-sm font-medium text-primary">Llamar · {selected.phone}</Text>
                        </Pressable>
                      ) : null}
                    </View>
                    <Link href={`/branch/${selected.id}`} asChild>
                      <Button>
                        <Text>Ordena ahora</Text>
                      </Button>
                    </Link>
                  </>
                ) : null}
                {loading ? <ActivityIndicator /> : null}
                {error ? (
                  <View className="items-center gap-3">
                    <Text className="text-center text-destructive">{error}</Text>
                    <Button onPress={reload}>
                      <Text>Reintentar</Text>
                    </Button>
                  </View>
                ) : null}
                {!loading && !error && !selected ? (
                  <Text className="text-muted-foreground">Este negocio aún no tiene sucursales activas.</Text>
                ) : null}
              </CardContent>
            </Card>

            {branches.length > 1 ? (
              <View className="gap-2">
                <Text className="text-xs uppercase tracking-widest text-muted-foreground">Tus sucursales</Text>
                {branches.map((branch) => (
                  <Card key={branch.id}>
                    <CardContent className="flex-row items-center justify-between gap-3 pt-6">
                      <View className="flex-1">
                        <Text className="font-semibold">{branch.name}</Text>
                        {branch.address ? <Text className="text-sm text-muted-foreground">{branch.address}</Text> : null}
                      </View>
                      <Button
                        size="sm"
                        variant={branch.id === selected?.id ? "secondary" : "outline"}
                        onPress={() => select(branch.id)}
                        disabled={branch.id === selected?.id}
                      >
                        <Text>{branch.id === selected?.id ? "Elegida" : "Elegir"}</Text>
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </View>
            ) : null}
          </View>
        )}
      </View>
    </ScrollView>
  );
}
