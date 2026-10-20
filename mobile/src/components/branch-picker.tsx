import { useBranches } from "@/lib/branch";
import { usePalette } from "@/lib/brand-provider";
import Ionicons from "@expo/vector-icons/Ionicons";
import { useState } from "react";
import { Modal, Pressable, View } from "react-native";

import { Text } from "./ui/text";

/** Fila "Sucursal: Centro ▾" que abre una lista para cambiarla. */
export function BranchPicker() {
  const { branches, selected, select } = useBranches();
  const palette = usePalette();
  const [open, setOpen] = useState(false);

  if (!selected) return null;
  return (
    <>
      <Pressable
        onPress={() => setOpen(true)}
        accessibilityRole="button"
        accessibilityLabel="Cambiar sucursal"
        className="flex-row items-center gap-2"
      >
        <Ionicons name="storefront-outline" size={20} color={palette.foreground} />
        <View>
          <Text className="text-xs text-muted-foreground">Sucursal</Text>
          <Text className="font-semibold">{selected.name}</Text>
        </View>
        <Ionicons name="chevron-down" size={16} color={palette.mutedForeground} />
      </Pressable>

      <Modal transparent animationType="fade" visible={open} onRequestClose={() => setOpen(false)}>
        <Pressable className="flex-1 items-center justify-center bg-black/50 p-6" onPress={() => setOpen(false)}>
          {/* Pressable interno: tocar la lista no cierra el modal. */}
          <Pressable className="w-full max-w-sm gap-1 rounded-2xl bg-background p-4">
            <Text className="mb-2 text-lg font-semibold">Elige tu sucursal</Text>
            {branches.map((branch) => (
              <Pressable
                key={branch.id}
                onPress={() => {
                  select(branch.id);
                  setOpen(false);
                }}
                accessibilityRole="button"
                className="flex-row items-center justify-between rounded-xl p-3 active:bg-muted"
              >
                <View className="flex-1">
                  <Text className="font-medium">{branch.name}</Text>
                  {branch.address ? <Text className="text-sm text-muted-foreground">{branch.address}</Text> : null}
                </View>
                {branch.id === selected.id ? <Ionicons name="checkmark" size={20} color={palette.primary} /> : null}
              </Pressable>
            ))}
          </Pressable>
        </Pressable>
      </Modal>
    </>
  );
}
