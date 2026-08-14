"use client";

import { useState } from "react";
import type {
  Deck,
  KnownVocabularyItem,
  NewVocabularyWord,
  VocabularyItem,
} from "@/lib/api/types";
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

// Known-vocabulary rows have no base_text to match against -- same
// identity the known-vocabulary system itself dedupes on
// (course_id, target_text).
function isAlreadyKnown(word: NewVocabularyWord, existingKnownWords: KnownVocabularyItem[]): boolean {
  const target = normalizeForComparison(word.target_text);
  return existingKnownWords.some((item) => normalizeForComparison(item.target_text) === target);
}

// Generic "you encountered this new word" row -- shared by reading-passage
// generation and paste-in unknown-word flagging. Two independent actions:
// "Add to deck" (a real flashcard, actively practiced via spaced
// repetition) and "Mark as known" (just an inventory note -- see the
// known-vocabulary system's own manual-add flow, which this reuses). A
// word can be neither, either, or both.
export function NewVocabularyRow({
  word,
  courseDecks,
  existingVocab,
  existingKnownWords,
  onAddToDeck,
  onMarkKnown,
}: {
  word: NewVocabularyWord;
  courseDecks: Deck[];
  existingVocab: VocabularyItem[];
  existingKnownWords: KnownVocabularyItem[];
  onAddToDeck: (word: NewVocabularyWord, deckId: string) => Promise<void>;
  onMarkKnown: (word: NewVocabularyWord) => Promise<void>;
}) {
  const [deckId, setDeckId] = useState(courseDecks[0]?.id ?? "");
  const [isAdding, setIsAdding] = useState(false);
  const [isMarkingKnown, setIsMarkingKnown] = useState(false);
  const selectedDeckId = deckId || courseDecks[0]?.id || "";
  const added = isAlreadyAdded(word, existingVocab);
  const known = isAlreadyKnown(word, existingKnownWords);

  async function handleAdd() {
    if (!selectedDeckId || added) return;
    setIsAdding(true);
    try {
      await onAddToDeck(word, selectedDeckId);
    } finally {
      setIsAdding(false);
    }
  }

  async function handleMarkKnown() {
    if (known) return;
    setIsMarkingKnown(true);
    try {
      await onMarkKnown(word);
    } finally {
      setIsMarkingKnown(false);
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
        <button
          type="button"
          onClick={handleMarkKnown}
          disabled={known || isMarkingKnown}
          className="rounded-md border border-line px-2 py-1 text-xs font-medium text-ink disabled:opacity-50"
        >
          {known ? "Known" : isMarkingKnown ? "Marking…" : "Mark as known"}
        </button>
      </div>
    </li>
  );
}
