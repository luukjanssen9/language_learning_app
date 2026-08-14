"use client";

import { useState } from "react";
import type { Deck, JournalEntry, VocabSuggestion, VocabularyItem } from "@/lib/api/types";
import { normalizeForComparison } from "@/lib/textNormalize";

// A suggestion counts as already-added when a VocabularyItem with the
// same target_text AND base_text (accent/case-insensitive) already
// exists in the course -- matching the backend's own quick-add dedup
// identity (2026-08-14). Checked against real data, not local-only
// state, since local state reset to "offered" on every page revisit and
// let the same suggestion be accepted twice (see PLAN.md's follow-up).
function isAlreadyAdded(suggestion: VocabSuggestion, existingVocab: VocabularyItem[]): boolean {
  const target = normalizeForComparison(suggestion.target_text);
  const base = normalizeForComparison(suggestion.base_text);
  return existingVocab.some(
    (item) =>
      normalizeForComparison(item.target_text) === target &&
      normalizeForComparison(item.base_text) === base,
  );
}

function VocabSuggestionRow({
  suggestion,
  courseDecks,
  existingVocab,
  onAddToDeck,
}: {
  suggestion: VocabSuggestion;
  courseDecks: Deck[];
  existingVocab: VocabularyItem[];
  onAddToDeck: (suggestion: VocabSuggestion, deckId: string) => Promise<void>;
}) {
  const [deckId, setDeckId] = useState(courseDecks[0]?.id ?? "");
  const [isAdding, setIsAdding] = useState(false);
  const selectedDeckId = deckId || courseDecks[0]?.id || "";
  // Reactive, not client-only: once onAddToDeck's mutation invalidates
  // the vocabulary-items query, this recomputes true on the next render.
  const added = isAlreadyAdded(suggestion, existingVocab);

  async function handleAdd() {
    if (!selectedDeckId || added) return;
    setIsAdding(true);
    try {
      await onAddToDeck(suggestion, selectedDeckId);
    } finally {
      setIsAdding(false);
    }
  }

  return (
    <li className="flex items-center justify-between gap-3 border-t border-line pt-2 first:border-t-0 first:pt-0">
      <div>
        <p className="text-ink">
          {suggestion.target_text} <span className="text-ink-soft">→</span>{" "}
          {suggestion.base_text}
        </p>
        <p className="text-sm text-ink-soft">{suggestion.example_sentence}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {courseDecks.length > 1 && !added && (
          <select
            value={selectedDeckId}
            onChange={(e) => setDeckId(e.target.value)}
            className="rounded-md border border-line bg-bg px-2 py-1 text-xs text-ink"
          >
            {courseDecks.map((deck) => (
              <option key={deck.id} value={deck.id}>
                {deck.name}
              </option>
            ))}
          </select>
        )}
        <button
          type="button"
          onClick={handleAdd}
          disabled={added || isAdding}
          className="rounded-md border border-line px-2 py-1 text-xs font-medium text-ink disabled:opacity-50"
        >
          {added ? "Added" : isAdding ? "Adding…" : "+ Add to deck"}
        </button>
      </div>
    </li>
  );
}

export function JournalEntryCard({
  entry,
  courseDecks,
  existingVocab,
  onAddToDeck,
}: {
  entry: JournalEntry;
  courseDecks: Deck[];
  existingVocab: VocabularyItem[];
  onAddToDeck: (suggestion: VocabSuggestion, deckId: string) => Promise<void>;
}) {
  return (
    <article className="flex flex-col gap-3 border border-line bg-surface p-4">
      <p className="text-ink-soft">{entry.submitted_text}</p>
      <p className="text-ink">{entry.corrected_text}</p>
      <p className="text-sm text-ink-soft">{entry.overall_feedback}</p>

      {entry.corrections.length > 0 && (
        <div className="flex flex-col gap-2">
          <h3 className="text-xs font-medium uppercase tracking-wide text-ink-soft">
            Corrections
          </h3>
          <ul className="flex flex-col gap-2">
            {entry.corrections.map((c, i) => (
              <li key={i} className="text-sm">
                <span className="text-rating-again line-through">{c.original}</span>{" "}
                <span className="text-rating-good">{c.corrected}</span>
                <p className="text-ink-soft">{c.explanation}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {entry.vocabulary_suggestions.length > 0 && (
        <div className="flex flex-col gap-2">
          <h3 className="text-xs font-medium uppercase tracking-wide text-ink-soft">
            New vocabulary
          </h3>
          <ul className="flex flex-col gap-2">
            {entry.vocabulary_suggestions.map((s, i) => (
              <VocabSuggestionRow
                key={i}
                suggestion={s}
                courseDecks={courseDecks}
                existingVocab={existingVocab}
                onAddToDeck={onAddToDeck}
              />
            ))}
          </ul>
        </div>
      )}
    </article>
  );
}
