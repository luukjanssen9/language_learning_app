"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { KnownVocabularyRow } from "@/components/knownVocabulary/KnownVocabularyRow";
import { useDecks } from "@/hooks/useDecks";
import {
  useAddKnownVocabulary,
  useDeleteKnownVocabulary,
  useKnownVocabularyItems,
  usePromoteKnownVocabulary,
} from "@/hooks/useKnownVocabulary";
import { getFrequencyBands } from "@/lib/frequencyBands";
import type { KnownVocabularyItem } from "@/lib/api/types";
import { useCourseContext } from "@/providers/CourseProvider";

export default function KnownVocabularyPage() {
  const { selectedCourseId, selectedTargetLanguage } = useCourseContext();
  const { data: decks = [] } = useDecks();
  const { data: items = [], isPending } = useKnownVocabularyItems(selectedCourseId);
  const addItem = useAddKnownVocabulary();
  const deleteItem = useDeleteKnownVocabulary();
  const promoteItem = usePromoteKnownVocabulary();

  const [newWord, setNewWord] = useState("");
  const [query, setQuery] = useState("");

  const courseDecks = decks.filter((d) => d.course_id === selectedCourseId);
  const hasPlacementCheck =
    selectedTargetLanguage !== undefined &&
    getFrequencyBands(selectedTargetLanguage.code) !== null;

  const filteredItems = items.filter((item) =>
    item.target_text.includes(query.trim().toLowerCase()),
  );

  function handleAdd(e: FormEvent) {
    e.preventDefault();
    const word = newWord.trim();
    if (!word) return;
    addItem.mutate(
      { course_id: selectedCourseId, target_text: word },
      { onSuccess: () => setNewWord("") },
    );
  }

  async function handlePromote(item: KnownVocabularyItem, deckId: string) {
    await promoteItem.mutateAsync({ id: item.id, deckId });
  }

  async function handleDelete(item: KnownVocabularyItem) {
    await deleteItem.mutateAsync({ id: item.id, courseId: selectedCourseId });
  }

  return (
    <div className="flex flex-col gap-6">
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

      {items.length > 0 && (
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
      {!isPending && items.length === 0 && (
        <p className="text-ink-soft">
          No known vocabulary yet — add a word above{hasPlacementCheck ? " or take the placement check" : ""}.
        </p>
      )}
      {!isPending && items.length > 0 && filteredItems.length === 0 && (
        <p className="text-ink-soft">No words match &quot;{query}&quot;.</p>
      )}
    </div>
  );
}
