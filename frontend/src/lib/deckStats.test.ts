import { describe, expect, it } from "vitest";
import { computeDeckStats } from "./deckStats";
import type { Card } from "./api/types";

const NOW = new Date("2026-08-13T12:00:00Z");

function makeCard(overrides: Partial<Card>): Card {
  return {
    id: crypto.randomUUID(),
    deck_id: "deck-1",
    vocabulary_item_id: null,
    front_override: "front",
    back_override: "back",
    direction: "target_to_base",
    created_at: NOW.toISOString(),
    state: "new",
    step: null,
    stability: null,
    difficulty: null,
    due_at: null,
    reps: 0,
    lapses: 0,
    last_reviewed_at: null,
    ...overrides,
  };
}

describe("computeDeckStats", () => {
  it("counts new cards as new, not due", () => {
    const cards = [makeCard({ state: "new" }), makeCard({ state: "new" })];
    const stats = computeDeckStats(cards, NOW);
    expect(stats.newCount).toBe(2);
    expect(stats.dueCount).toBe(0);
    expect(stats.totalCards).toBe(2);
  });

  it("counts a learning card past its due_at as due", () => {
    const cards = [
      makeCard({ state: "learning", due_at: new Date(NOW.getTime() - 60_000).toISOString() }),
    ];
    const stats = computeDeckStats(cards, NOW);
    expect(stats.dueCount).toBe(1);
  });

  it("does not count a card due in the future as due", () => {
    const cards = [
      makeCard({ state: "review", due_at: new Date(NOW.getTime() + 60_000).toISOString() }),
    ];
    const stats = computeDeckStats(cards, NOW);
    expect(stats.dueCount).toBe(0);
  });

  it("computes progress as the share of cards not in new state", () => {
    const cards = [
      makeCard({ state: "new" }),
      makeCard({ state: "review" }),
      makeCard({ state: "learning" }),
      makeCard({ state: "review" }),
    ];
    const stats = computeDeckStats(cards, NOW);
    expect(stats.progress).toBeCloseTo(0.75);
  });

  it("returns zero progress for an empty deck without dividing by zero", () => {
    const stats = computeDeckStats([], NOW);
    expect(stats.progress).toBe(0);
    expect(stats.totalCards).toBe(0);
  });
});
