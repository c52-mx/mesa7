import type { Loyalty } from "./api";

/** Avance (0 a 1) desde el último hito desbloqueado hacia el siguiente. 1 si ya no hay más. */
export function rewardProgress(loyalty: Loyalty): number {
  const next = loyalty.next_reward;
  if (!next) return 1;
  const previous = [...loyalty.rewards].reverse().find((r) => r.unlocked)?.points_required ?? 0;
  return (loyalty.points - previous) / (next.points_required - previous);
}

/** "123456789012" -> "1234 5678 9012" */
export function formatMemberCode(code: string): string {
  return code.replace(/(\d{4})(?=\d)/g, "$1 ");
}
