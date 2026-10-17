// Marca blanca: de dos colores del tenant se deriva todo el tema (claro y oscuro).

type RGB = [number, number, number];

const clamp = (n: number) => Math.min(255, Math.max(0, Math.round(n)));

function hexToRgb(hex: string): RGB {
  const value = hex.replace("#", "");
  return [0, 2, 4].map((i) => parseInt(value.slice(i, i + 2), 16)) as RGB;
}

function rgbToHex([r, g, b]: RGB): string {
  return "#" + [r, g, b].map((n) => clamp(n).toString(16).padStart(2, "0")).join("");
}

/** a*(1-t) + b*t */
export function mix(a: string, b: string, t: number): string {
  const [ra, rb] = [hexToRgb(a), hexToRgb(b)];
  return rgbToHex(ra.map((v, i) => v * (1 - t) + rb[i] * t) as RGB);
}

function luminance(hex: string): number {
  const [r, g, b] = hexToRgb(hex).map((v) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

/** Texto legible sobre un color de fondo (blanco u oscuro, el de mayor contraste). */
export function onColor(background: string): string {
  return contrast(background, "#FFFFFF") >= contrast(background, "#1A1A1A") ? "#FFFFFF" : "#1A1A1A";
}

export type Palette = Record<
  | "background" | "foreground" | "card" | "cardForeground" | "popover" | "popoverForeground"
  | "primary" | "primaryForeground" | "secondary" | "secondaryForeground"
  | "muted" | "mutedForeground" | "accent" | "accentForeground"
  | "destructive" | "border" | "input" | "ring",
  string
>;

export function brandPalette(primary: string, secondary: string, mode: "light" | "dark"): Palette {
  const white = "#FFFFFF";
  const black = "#000000";
  if (mode === "light") {
    const foreground = mix(secondary, black, 0.65);
    const border = mix(secondary, white, 0.88);
    return {
      background: white,
      foreground,
      card: white,
      cardForeground: foreground,
      popover: white,
      popoverForeground: foreground,
      primary,
      primaryForeground: onColor(primary),
      secondary,
      secondaryForeground: onColor(secondary),
      muted: mix(secondary, white, 0.94),
      mutedForeground: mix(secondary, white, 0.3),
      accent: mix(primary, white, 0.85),
      accentForeground: foreground,
      destructive: "#DC2626",
      border,
      input: border,
      ring: primary,
    };
  }
  const foreground = "#FAF5F0";
  const card = mix(secondary, black, 0.78);
  const border = mix(secondary, black, 0.55);
  return {
    background: mix(secondary, black, 0.86),
    foreground,
    card,
    cardForeground: foreground,
    popover: card,
    popoverForeground: foreground,
    primary,
    primaryForeground: onColor(primary),
    secondary: mix(secondary, black, 0.4),
    secondaryForeground: foreground,
    muted: mix(secondary, black, 0.7),
    mutedForeground: "#C9B8B0",
    accent: mix(primary, black, 0.7),
    accentForeground: foreground,
    destructive: "#F87171",
    border,
    input: border,
    ring: primary,
  };
}

function toHslTriplet(hex: string): string {
  const [r, g, b] = hexToRgb(hex).map((v) => v / 255);
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const l = (max + min) / 2;
  const d = max - min;
  let h = 0;
  let s = 0;
  if (d !== 0) {
    s = d / (1 - Math.abs(2 * l - 1));
    if (max === r) h = ((g - b) / d) % 6;
    else if (max === g) h = (b - r) / d + 2;
    else h = (r - g) / d + 4;
    h *= 60;
    if (h < 0) h += 360;
  }
  return `${Math.round(h)} ${Math.round(s * 100)}% ${Math.round(l * 100)}%`;
}

const kebab = (key: string) => key.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());

/** Variables CSS que usan los componentes (bg-primary, text-foreground, ...). */
export function paletteVars(palette: Palette): Record<string, string> {
  return Object.fromEntries(
    Object.entries(palette).map(([key, hex]) => [`--${kebab(key)}`, toHslTriplet(hex)]),
  );
}

export function isHex(value: string): boolean {
  return /^#[0-9a-fA-F]{6}$/.test(value);
}
