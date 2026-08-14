"use client";

import { useState } from "react";
import type { Deck, KnownVocabularyItem } from "@/lib/api/types";

const SOURCE_LABELS: Record<KnownVocabularyItem["source"], string> = {
  placement_check: "Placement check",
  manual: "Manual",
  promoted: "Promoted",
};

// Presentational/callback-driven, same split as VocabSuggestionRow
// (components/journal/JournalEntryCard.tsx): no hook wiring here, so this
// is unit-testable without mocking TanStack Query -- the real hooks are
// wired one level up in the known-vocabulary page.
export function KnownVocabularyRow({
  item,
  decks,
  onPromote,
  onDelete,
}: {
  item: KnownVocabularyItem;
  decks: Deck[];
  onPromote: (item: KnownVocabularyItem, deckId: string) => Promise<void>;
  onDelete: (item: KnownVocabularyItem) => Promise<void>;
}) {
  const [deckId, setDeckId] = useState(decks[0]?.id ?? "");
  const [isPromoting, setIsPromoting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const selectedDeckId = deckId || decks[0]?.id || "";
  const promoted = item.source === "promoted";

  async function handlePromote() {
    if (!selectedDeckId || promoted) return;
    setIsPromoting(true);
    try {
      await onPromote(item, selectedDeckId);
    } finally {
      setIsPromoting(false);
    }
  }

  async function handleDelete() {
    setIsDeleting(true);
    try {
      await onDelete(item);
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <li className="flex items-center justify-between gap-3 border-t border-line pt-2 first:border-t-0 first:pt-0">
      <div>
        <p className="text-ink">{item.target_text}</p>
        <p className="text-xs text-ink-soft">{SOURCE_LABELS[item.source]}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {!promoted && decks.length > 1 && (
          <select
            value={selectedDeckId}
            onChange={(e) => setDeckId(e.target.value)}
            className="rounded-md border border-line bg-bg px-2 py-1 text-xs text-ink"
          >
            {decks.map((deck) => (
              <option key={deck.id} value={deck.id}>
                {deck.name}
              </option>
            ))}
          </select>
        )}
        {!promoted && (
          <button
            type="button"
            onClick={handlePromote}
            disabled={isPromoting || !selectedDeckId}
            className="rounded-md border border-line px-2 py-1 text-xs font-medium text-ink disabled:opacity-50"
          >
            {isPromoting ? "Promoting…" : "Promote"}
          </button>
        )}
        <button
          type="button"
          onClick={handleDelete}
          disabled={isDeleting}
          className="rounded-md px-2 py-1 text-xs text-ink-soft disabled:opacity-50"
        >
          {isDeleting ? "…" : "Remove"}
        </button>
      </div>
    </li>
  );
}
