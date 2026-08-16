"use client";

import { useState, type FormEvent } from "react";
import { JournalEntryCard } from "@/components/journal/JournalEntryCard";
import { useDecks } from "@/hooks/useDecks";
import { useJournalEntries, useSubmitJournalEntry } from "@/hooks/useJournal";
import { useQuickAddCard } from "@/hooks/useQuickAddCard";
import { useVocabularyItems } from "@/hooks/useVocabulary";
import type { VocabSuggestion } from "@/lib/api/types";
import { useCourseContext } from "@/providers/CourseProvider";

export default function JournalPage() {
  const { selectedCourseId } = useCourseContext();
  const { data: decks = [] } = useDecks();
  const { data: entries = [], isPending } = useJournalEntries(selectedCourseId);
  const { data: vocabItems = [] } = useVocabularyItems(selectedCourseId);
  const submitEntry = useSubmitJournalEntry();
  const quickAdd = useQuickAddCard();

  const [text, setText] = useState("");

  const courseDecks = decks.filter((d) => d.course_id === selectedCourseId);

  async function handleAddToDeck(suggestion: VocabSuggestion, deckId: string) {
    await quickAdd.mutateAsync({
      deck_id: deckId,
      target_text: suggestion.target_text,
      base_text: suggestion.base_text,
      example_sentence: suggestion.example_sentence,
      source: "Journal entry",
    });
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    submitEntry.mutate(
      { course_id: selectedCourseId, text: text.trim() },
      { onSuccess: () => setText("") },
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={5}
          placeholder="Write a few sentences in your target language…"
          disabled={submitEntry.isPending}
          className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
        />
        {submitEntry.isError && (
          <p className="text-sm text-rating-again">Couldn&apos;t get feedback. Try again.</p>
        )}
        <button
          type="submit"
          disabled={submitEntry.isPending || !text.trim()}
          className="self-start rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg disabled:opacity-50"
        >
          {submitEntry.isPending ? "Grading…" : "Get feedback"}
        </button>
      </form>

      <div className="flex flex-col gap-3">
        {entries.map((entry) => (
          <JournalEntryCard
            key={entry.id}
            entry={entry}
            courseDecks={courseDecks}
            existingVocab={vocabItems}
            onAddToDeck={handleAddToDeck}
          />
        ))}
        {!isPending && entries.length === 0 && (
          <p className="text-ink-soft">No journal entries yet — write your first one above.</p>
        )}
      </div>
    </div>
  );
}
