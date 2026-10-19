import { useBrand } from "@/lib/brand-provider";
import type { ReactNode } from "react";
import { Image, KeyboardAvoidingView, Platform, ScrollView, View } from "react-native";

import { Text } from "./ui/text";

/** Marco común de login y registro: logo y nombre del negocio, y el formulario debajo. */
export function AuthScreen({ title, children }: { title: string; children: ReactNode }) {
  const brand = useBrand();
  return (
    <KeyboardAvoidingView
      className="flex-1 bg-background"
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView
        contentContainerClassName="flex-grow items-center justify-center p-6"
        keyboardShouldPersistTaps="handled"
      >
        {/* Ancho máximo: en tablet o web el formulario no se estira a toda la pantalla. */}
        <View className="w-full max-w-md gap-6">
          <View className="items-center gap-3">
            {brand.logo_url ? (
              <Image source={{ uri: brand.logo_url }} className="h-28 w-28" resizeMode="contain" />
            ) : null}
            <Text className="text-3xl font-bold">{brand.name}</Text>
            <Text className="text-lg text-muted-foreground">{title}</Text>
          </View>
          {children}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
