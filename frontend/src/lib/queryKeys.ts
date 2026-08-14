export const queryKeys = {
  courses: ["courses"] as const,
  languages: ["languages"] as const,

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

  skills: (courseId: string) => ["skills", courseId] as const,
  // A lesson session fetches its exercise queue once (staleTime: Infinity)
  // and freezes it locally, same as dueCards above. Kept under its own
  // top-level "skills" root rather than nested under `progress` below, so
  // invalidating progress after an attempt can never prefix-match and
  // silently refetch/reshuffle a session's in-progress exercise queue.
  exercises: (skillId: string) => ["skills", skillId, "exercises"] as const,
  progress: (userId: string) => ["user-progress", userId] as const,

  vocabulary: (courseId: string) => ["vocabulary-items", courseId] as const,
  // Generated content is immutable once cached (see the backend's
  // get-or-generate `VocabularyExample` endpoint) -- nothing else in this
  // app should ever invalidate it, so it doesn't need the same
  // sibling-vs-nested care dueCards/exercises document above; it's simply
  // its own leaf, keyed off the vocabulary item rather than the course.
  vocabularyExamples: (vocabularyItemId: string) =>
    ["vocabulary-items", vocabularyItemId, "examples"] as const,

  journalEntries: (userId: string, courseId: string) =>
    ["journal-entries", userId, courseId] as const,

  knownVocabulary: (courseId: string) => ["known-vocabulary", courseId] as const,

  readingPassages: (courseId: string) => ["reading-passages", courseId] as const,
};
