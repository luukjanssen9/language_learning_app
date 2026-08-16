"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { CoveragePanel } from "@/components/knownVocabulary/CoveragePanel";
import { KnownVocabularyRow } from "@/components/knownVocabulary/KnownVocabularyRow";
import { MasteredVocabularyRow } from "@/components/knownVocabulary/MasteredVocabularyRow";
import { useDecks } from "@/hooks/useDecks";
import {
  useAddKnownVocabulary,
  useDeleteKnownVocabulary,
  useKnownVocabularyItems,
  useKnownWordSet,
  useMasteredVocabulary,
  usePromoteKnownVocabulary,
} from "@/hooks/useKnownVocabulary";
import { computeCoverage } from "@/lib/coverageAnalysis";
import { getFrequencyBands } from "@/lib/frequencyBands";
import { normalizeForComparison } from "@/lib/textNormalize";
import type { KnownVocabularyItem } from "@/lib/api/types";
import { useBootstrapContext } from "@/providers/BootstrapProvider";
import { useCourseContext } from "@/providers/CourseProvider";

export default function KnownVocabularyPage() {
  const { userId } = useBootstrapContext();
  const { selectedCourseId, selectedTargetLanguage } = useCourseContext();
  const { data: decks = [] } = useDecks();
  const { data: items = [], isPending } = useKnownVocabularyItems(selectedCourseId, userId);
  const { data: fullSet } = useKnownWordSet(selectedCourseId, userId);
  const { data: masteredWords = [] } = useMasteredVocabulary(selectedCourseId, userId);
  const addItem = useAddKnownVocabulary();
  const deleteItem = useDeleteKnownVocabulary();
  const promoteItem = usePromoteKnownVocabulary();

  const [newWord, setNewWord] = useState("");
  const [query, setQuery] = useState("");

  const courseDecks = decks.filter((d) => d.course_id === selectedCourseId);
  const bands = selectedTargetLanguage ? getFrequencyBands(selectedTargetLanguage.code) : null;
  const hasPlacementCheck = bands !== null;

  const filteredItems = items.filter((item) =>
    item.target_text.includes(query.trim().toLowerCase()),
  );

  // Words mastered purely through normal deck review, never touched via
  // the known-vocabulary system at all (placement check, manual add, or
  // promotion) -- otherwise they'd count as "known" everywhere the AI
  // features look (see get_full_known_word_set) but never actually show
  // up on this page. Deduped against `items` by normalized target_text
  // since a promoted word that's since been mastered would otherwise
  // appear twice.
  const trackedTargetTexts = new Set(items.map((item) => normalizeForComparison(item.target_text)));
  const untrackedMasteredWords = masteredWords.filter(
    (word) => !trackedTargetTexts.has(normalizeForComparison(word.target_text)),
  );
  // Same plain lowercase-includes search as filteredItems above, not
  // normalizeForComparison -- kept consistent with the existing search
  // box's behavior rather than quietly upgrading only this section.
  const filteredMasteredWords = untrackedMasteredWords.filter((word) =>
    word.target_text.toLowerCase().includes(query.trim().toLowerCase()),
  );

  function handleAdd(e: FormEvent) {
    e.preventDefault();
    const word = newWord.trim();
    if (!word) return;
    addItem.mutate(
      { course_id: selectedCourseId, user_id: userId, target_text: word },
      { onSuccess: () => setNewWord("") },
    );
  }

  async function handlePromote(item: KnownVocabularyItem, deckId: string) {
    await promoteItem.mutateAsync({ id: item.id, deckId });
  }

  async function handleDelete(item: KnownVocabularyItem) {
    await deleteItem.mutateAsync({ id: item.id, courseId: selectedCourseId, userId });
  }

  return (
    <div className="flex flex-col gap-6">
      {bands && fullSet && (
        <CoveragePanel coverage={computeCoverage(bands, fullSet.words)} />
      )}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <form onSubmit={handleAdd} className="flex gap-2">
          <input
            value={newWord}
            onChange={(e) => setNewWord(e.target.value)}
            placeholder="Add a word you already know…"
            className="rounded-md border border-line bg-bg px-3 py-2 text-sm text-ink"
          />
          <button
            type="submit"
            disabled={addItem.isPending || !newWord.trim()}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg disabled:opacity-50"
          >
            Add
          </button>
        </form>
        {hasPlacementCheck && (
          <Link
            href="/known-vocabulary/placement-check"
            className="rounded-md border border-line px-4 py-2 text-center text-sm font-medium text-ink"
          >
            Take placement check
          </Link>
        )}
      </div>

      {(items.length > 0 || untrackedMasteredWords.length > 0) && (
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search…"
          className="rounded-md border border-line bg-bg px-3 py-2 text-sm text-ink"
        />
      )}

      <ul className="flex flex-col gap-2">
        {filteredItems.map((item) => (
          <KnownVocabularyRow
            key={item.id}
            item={item}
            decks={courseDecks}
            onPromote={handlePromote}
            onDelete={handleDelete}
          />
        ))}
      </ul>
      {!isPending && items.length === 0 && untrackedMasteredWords.length === 0 && (
        <p className="text-ink-soft">
          No known vocabulary yet — add a word above{hasPlacementCheck ? " or take the placement check" : ""}.
        </p>
      )}
      {!isPending && items.length > 0 && filteredItems.length === 0 && (
        <p className="text-ink-soft">
          {/* Distinguished from a flat "No words match" -- otherwise this
          reads as contradicting the Mastered flashcards section right
          below it when a query matches there but not here. */}
          No tracked words match &quot;{query}&quot;
          {filteredMasteredWords.length > 0 ? " (see Mastered flashcards below)" : ""}.
        </p>
      )}

      {filteredMasteredWords.length > 0 && (
        <div className="flex flex-col gap-2">
          <h2 className="text-xs font-medium uppercase tracking-wide text-ink-soft">
            Mastered flashcards
          </h2>
          <ul className="flex flex-col gap-2">
            {filteredMasteredWords.map((word) => (
              <MasteredVocabularyRow key={word.id} item={word} />
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
