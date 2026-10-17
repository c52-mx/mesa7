// Para probar con un teléfono contra la computadora usa la IP de tu red (http://192.168.x.x:8000).
export const API_URL = (process.env.EXPO_PUBLIC_API_URL ?? "http://31.220.60.177:8010").replace(/\/$/, "");

// Negocio (tenant) al que se conecta esta app.
export const TENANT_SLUG = process.env.EXPO_PUBLIC_TENANT ?? "demo";
