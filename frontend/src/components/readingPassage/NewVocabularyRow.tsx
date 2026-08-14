"use client";

import { useState } from "react";
import type { Deck, NewVocabularyWord, VocabularyItem } from "@/lib/api/types";
import { normalizeForComparison } from "@/lib/textNormalize";

// Same identity/derivation as JournalEntryCard.tsx's isAlreadyAdded --
// "added" must come from the real vocabulary list, not local-only state
// that resets on remount, per the duplicate-vocab bug that pattern was
// fixed for (2026-08-14).
function isAlreadyAdded(word: NewVocabularyWord, existingVocab: VocabularyItem[]): boolean {
  const target = normalizeForComparison(word.target_text);
  const base = normalizeForComparison(word.base_text);
  return existingVocab.some(
    (item) =>
      normalizeForComparison(item.target_text) === target &&
      normalizeForComparison(item.base_text) === base,
  );
}

export function NewVocabularyRow({
  word,
  courseDecks,
  existingVocab,
  onAddToDeck,
}: {
  word: NewVocabularyWord;
  courseDecks: Deck[];
  existingVocab: VocabularyItem[];
  onAddToDeck: (word: NewVocabularyWord, deckId: string) => Promise<void>;
}) {
  const [deckId, setDeckId] = useState(courseDecks[0]?.id ?? "");
  const [isAdding, setIsAdding] = useState(false);
  const selectedDeckId = deckId || courseDecks[0]?.id || "";
  const added = isAlreadyAdded(word, existingVocab);

  async function handleAdd() {
    if (!selectedDeckId || added) return;
    setIsAdding(true);
    try {
      await onAddToDeck(word, selectedDeckId);
    } finally {
      setIsAdding(false);
    }
  }

  return (
    <li className="flex items-center justify-between gap-3 border-t border-line pt-2 first:border-t-0 first:pt-0">
      <p className="text-ink">
        {word.target_text} <span className="text-ink-soft">→</span> {word.base_text}
      </p>
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
