/** "55.00" -> "$55.00" (pesos). */
export function money(value: string | number): string {
  const n = typeof value === "string" ? Number(value) : value;
  return `$${n.toFixed(2)}`;
}

/** Hora local corta, por ejemplo "4:35 p. m.". */
export function timeOf(iso: string): string {
  return new Date(iso).toLocaleTimeString("es-MX", { hour: "numeric", minute: "2-digit" });
}
