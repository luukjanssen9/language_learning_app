import { describe, expect, it } from "vitest";
import { formatCardStatus } from "./format";
import type { Card } from "./api/types";

const NOW = new Date("2026-08-14T12:00:00Z");

function makeCard(overrides: Partial<Card>): Card {
  return {
    id: "card-1",
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
    vocabulary_item: null,
    ...overrides,
  };
}

describe("formatCardStatus", () => {
  it("labels a new card as New", () => {
    expect(formatCardStatus(makeCard({ state: "new" }), NOW)).toBe("New");
  });

  it("labels a suspended card as Locked, not New, despite both having a null due_at", () => {
    expect(formatCardStatus(makeCard({ state: "suspended", due_at: null }), NOW)).toBe("Locked");
  });

  it("labels a learning card past its due_at as Due now", () => {
    const dueAt = new Date(NOW.getTime() - 60_000).toISOString();
    expect(formatCardStatus(makeCard({ state: "learning", due_at: dueAt }), NOW)).toBe("Due now");
  });

  it("labels a review card due in a few minutes accordingly", () => {
    const dueAt = new Date(NOW.getTime() + 5 * 60_000).toISOString();
    expect(formatCardStatus(makeCard({ state: "review", due_at: dueAt }), NOW)).toBe(
      "Due in 5 mins",
    );
  });

  it("labels a review card due in a few days accordingly", () => {
    const dueAt = new Date(NOW.getTime() + 3 * 24 * 60 * 60_000).toISOString();
    expect(formatCardStatus(makeCard({ state: "review", due_at: dueAt }), NOW)).toBe(
      "Due in 3 days",
    );
  });
});
