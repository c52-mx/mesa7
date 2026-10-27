import { BranchPicker } from "@/components/branch-picker";
import { Segmented } from "@/components/segmented";
import { Card, CardContent } from "@/components/ui/card";
import { Text } from "@/components/ui/text";
import { api, errorMessage, type StaffBanner, type StaffProduct } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useBranches } from "@/lib/branch";
import { usePalette } from "@/lib/brand-provider";
import { useApi } from "@/lib/use-api";
import { useState } from "react";
import { ActivityIndicator, Alert, ScrollView, Switch, View } from "react-native";

type Section = "stock" | "promos";

/** Una fila con interruptor: el cambio se guarda al momento y se revierte si el servidor lo rechaza. */
function ToggleRow({ title, subtitle, value, onChange }: { title: string; subtitle?: string; value: boolean; onChange: (v: boolean) => void }) {
  const palette = usePalette();
  return (
    <View className="flex-row items-center justify-between gap-3 border-b border-border py-3">
      <View className="flex-1">
        <Text className="font-semibold">{title}</Text>
        {subtitle ? <Text className="text-sm text-muted-foreground">{subtitle}</Text> : null}
      </View>
      <Switch value={value} onValueChange={onChange} trackColor={{ true: palette.primary }} />
    </View>
  );
}

function Stock() {
  const { selected } = useBranches();
  const list = useApi<StaffProduct[]>(selected ? `/api/staff/availability/?branch=${selected.id}` : null);
  const [overrides, setOverrides] = useState<Record<number, boolean>>({});

  async function toggle(product: StaffProduct, is_available: boolean) {
    if (!selected) return;
    setOverrides((o) => ({ ...o, [product.id]: is_available }));
    try {
      await api("/api/staff/availability/set/", { method: "POST", body: { branch: selected.id, product: product.id, is_available } });
      await list.reload();
    } catch (e) {
      Alert.alert("No se pudo guardar", errorMessage(e));
    } finally {
      setOverrides((o) => {
        const { [product.id]: _, ...rest } = o;
        return rest;
      });
    }
  }

  if (list.loading) return <ActivityIndicator className="py-8" />;
  if (list.error) return <Text className="py-8 text-center text-destructive">{list.error}</Text>;
  return (
    <Card>
      <CardContent className="pt-2">
        <Text className="py-2 text-sm text-muted-foreground">Apaga un producto cuando se agote en esta sucursal; deja de verse en la app al instante.</Text>
        {(list.data ?? []).map((p) => (
          <ToggleRow key={p.id} title={p.name} subtitle={p.category} value={overrides[p.id] ?? p.is_available} onChange={(v) => toggle(p, v)} />
        ))}
      </CardContent>
    </Card>
  );
}

function Promos() {
  const list = useApi<StaffBanner[]>("/api/staff/banners/");
  const [overrides, setOverrides] = useState<Record<number, boolean>>({});

  async function toggle(banner: StaffBanner, is_active: boolean) {
    setOverrides((o) => ({ ...o, [banner.id]: is_active }));
    try {
      await api(`/api/staff/banners/${banner.id}/`, { method: "PATCH", body: { is_active } });
      await list.reload();
    } catch (e) {
      Alert.alert("No se pudo guardar", errorMessage(e));
    } finally {
      setOverrides((o) => {
        const { [banner.id]: _, ...rest } = o;
        return rest;
      });
    }
  }

  if (list.loading) return <ActivityIndicator className="py-8" />;
  if (list.error) return <Text className="py-8 text-center text-destructive">{list.error}</Text>;
  return (
    <Card>
      <CardContent className="pt-2">
        <Text className="py-2 text-sm text-muted-foreground">Las promociones activas aparecen en el Inicio de los clientes. Para crear o editar textos usa el panel de administración.</Text>
        {(list.data ?? []).length === 0 ? <Text className="py-6 text-center text-muted-foreground">No hay promociones creadas.</Text> : null}
        {(list.data ?? []).map((b) => (
          <ToggleRow key={b.id} title={b.title} subtitle={b.text} value={overrides[b.id] ?? b.is_active} onChange={(v) => toggle(b, v)} />
        ))}
      </CardContent>
    </Card>
  );
}

export default function Catalog() {
  const { isOwner } = useAuth();
  const [section, setSection] = useState<Section>("stock");

  return (
    <ScrollView className="flex-1 bg-background" contentContainerClassName="items-center px-4 pb-8 pt-14">
      <View className="w-full max-w-2xl gap-4">
        <View className="flex-row items-end justify-between gap-3">
          <Text className="text-3xl font-bold">Catálogo</Text>
          {section === "stock" ? <BranchPicker /> : null}
        </View>
        {isOwner ? (
          <Segmented
            options={[
              { value: "stock", label: "Inventario" },
              { value: "promos", label: "Promociones" },
            ]}
            value={section}
            onChange={setSection}
          />
        ) : null}
        {section === "promos" && isOwner ? <Promos /> : <Stock />}
      </View>
    </ScrollView>
  );
}
