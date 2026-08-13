export const queryKeys = {
  decks: ["decks"] as const,
  deck: (id: string) => ["decks", id] as const,
  cards: (deckId: string) => ["decks", deckId, "cards"] as const,
  // Sibling to `cards`, deliberately not nested under it: TanStack Query's
  // invalidateQueries matches by key *prefix*. If this were
  // ["decks", deckId, "cards", "due"], invalidating `cards` after a review
  // (to refresh the deck-management page and dashboard progress bars) would
  // also silently refetch the due-queue a review session is actively
  // iterating over, reshuffling or dropping cards mid-session as ratings
  // reschedule them server-side. Keeping them siblings makes that
  // impossible by construction.
  dueCards: (deckId: string) => ["decks", deckId, "due-cards"] as const,
};
