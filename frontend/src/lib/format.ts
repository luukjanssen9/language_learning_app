import type { Card } from "./api/types";

/** Human-readable status for a card in a management list -- "New",
 * "Due now", or "Due in N day(s)". Pure and independently testable. */
export function formatCardStatus(card: Card, now: Date = new Date()): string {
  if (card.state === "new" || card.due_at === null) return "New";

  const dueAt = new Date(card.due_at);
  const diffMs = dueAt.getTime() - now.getTime();
  if (diffMs <= 0) return "Due now";

  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays < 1) {
    const diffMinutes = Math.ceil(diffMs / (1000 * 60));
    return `Due in ${diffMinutes} min${diffMinutes === 1 ? "" : "s"}`;
  }
  return `Due in ${diffDays} day${diffDays === 1 ? "" : "s"}`;
}
