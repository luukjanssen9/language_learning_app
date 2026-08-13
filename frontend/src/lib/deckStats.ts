import type { Card } from "./api/types";

export interface DeckStats {
  totalCards: number;
  dueCount: number;
  newCount: number;
  /** 0..1 -- share of cards not in "new" state. A simplification, not real
   * mastery scoring: no `UserProgress`/mastery data exists for decks yet
   * (that table is Skill-scoped, Phase 4 territory), and this doesn't
   * factor in FSRS's own stability-based recall-strength signal. Revisit
   * with a real metric once Phase 4 or a backend aggregate makes one
   * available. */
  progress: number;
}

export function computeDeckStats(cards: Card[], now: Date = new Date()): DeckStats {
  const newCount = cards.filter((c) => c.state === "new").length;
  const dueCount = cards.filter(
    (c) => c.state !== "new" && c.due_at !== null && new Date(c.due_at) <= now,
  ).length;
  return {
    totalCards: cards.length,
    dueCount,
    newCount,
    progress: cards.length === 0 ? 0 : (cards.length - newCount) / cards.length,
  };
}
