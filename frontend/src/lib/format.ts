import type { Card } from "./api/types";

/** Human-readable status for a card in a management list -- "New",
 * "Locked", "Due now", or "Due in N day(s)". Pure and independently
 * testable. */
export function formatCardStatus(card: Card, now: Date = new Date()): string {
  // Checked before the `due_at === null` fallback below -- a SUSPENDED
  // card also has a null due_at (never scheduled yet), and would
  // otherwise be mislabeled "New" even though it isn't reviewable until
  // its production gate is met (see PLAN.md's 2026-08-14 "Anki-style
  // vocab decks" decision).
  if (card.state === "suspended") return "Locked";
  if (card.state === "new" || card.due_at === null) return "New";

  const dueAt = new Date(card.due_at);
  const diffMs = dueAt.getTime() - now.getTime();
  if (diffMs <= 0) return "Due now";

  // Compared against the raw duration, not a Math.ceil'd day count first --
  // ceil-ing any sub-day duration always yields exactly 1, so checking
  // `diffDays < 1` afterward could never be true and the minutes branch
  // was unreachable dead code (found while adding test coverage here for
  // the "suspended" fix above; a card due in 5 minutes was showing "Due
  // in 1 day").
  const oneDayMs = 1000 * 60 * 60 * 24;
  if (diffMs < oneDayMs) {
    const diffMinutes = Math.ceil(diffMs / (1000 * 60));
    return `Due in ${diffMinutes} min${diffMinutes === 1 ? "" : "s"}`;
  }
  const diffDays = Math.ceil(diffMs / oneDayMs);
  return `Due in ${diffDays} day${diffDays === 1 ? "" : "s"}`;
}
