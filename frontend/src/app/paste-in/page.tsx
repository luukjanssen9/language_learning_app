"use client";

import { useState, type FormEvent } from "react";
import { NewVocabularyRow } from "@/components/vocabulary/NewVocabularyRow";
import { useDecks } from "@/hooks/useDecks";
import { useAnalyzePasteIn, useTranslateUnknownWords } from "@/hooks/usePasteIn";
import { useQuickAddCard } from "@/hooks/useQuickAddCard";
import { useVocabularyItems } from "@/hooks/useVocabulary";
import type { NewVocabularyWord } from "@/lib/api/types";
import { useCourseContext } from "@/providers/CourseProvider";

export default function PasteInPage() {
  const { selectedCourseId } = useCourseContext();
  const { data: decks = [] } = useDecks();
  const { data: vocabItems = [] } = useVocabularyItems(selectedCourseId);
  const quickAdd = useQuickAddCard();
  const analyze = useAnalyzePasteIn();
  const translate = useTranslateUnknownWords();

  const [text, setText] = useState("");

  const courseDecks = decks.filter((d) => d.course_id === selectedCourseId);

  async function handleAnalyze(e: FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    translate.reset(); // clear any stale glossary from a previous analysis
    const result = await analyze.mutateAsync({ course_id: selectedCourseId, text });
    if (result.unknown_words.length > 0) {
      translate.mutate({ course_id: selectedCourseId, words: result.unknown_words });
    }
  }

  async function handleAddToDeck(word: NewVocabularyWord, deckId: string) {
    await quickAdd.mutateAsync({
      deck_id: deckId,
      target_text: word.target_text,
      base_text: word.base_text,
      source: "Paste-in",
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <form onSubmit={handleAnalyze} className="flex flex-col gap-3">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={8}
          placeholder="Paste something you're reading in the target language…"
          disabled={analyze.isPending}
          className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
        />
        {analyze.isError && (
          <p className="text-sm text-rating-again">Couldn&apos;t analyze that text. Try again.</p>
        )}
        <button
          type="submit"
          disabled={analyze.isPending || !text.trim()}
          className="self-start rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg disabled:opacity-50"
        >
          {analyze.isPending ? "Analyzing…" : "Analyze"}
        </button>
      </form>

      {analyze.data && (
        <div className="flex flex-col gap-2">
          <p className="whitespace-pre-wrap text-lg text-ink">
            {analyze.data.segments.map((segment, i) =>
              segment.is_word && !segment.is_known ? (
                <span key={i} className="bg-accent/20 underline decoration-accent">
                  {segment.text}
                </span>
              ) : (
                <span key={i}>{segment.text}</span>
              ),
            )}
          </p>
        </div>
      )}

      {analyze.data && analyze.data.unknown_words.length > 0 && (
        <div className="flex flex-col gap-2">
          <h3 className="text-xs font-medium uppercase tracking-wide text-ink-soft">
            New vocabulary
          </h3>
          {translate.isPending && <p className="text-sm text-ink-soft">Loading translations…</p>}
          {translate.isError && (
            <p className="text-sm text-rating-again">Couldn&apos;t load translations.</p>
          )}
          {translate.data && (
            <ul className="flex flex-col gap-2">
              {translate.data.translations.map((word, i) => (
                <NewVocabularyRow
                  key={i}
                  word={word}
                  courseDecks={courseDecks}
                  existingVocab={vocabItems}
                  onAddToDeck={handleAddToDeck}
                />
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
