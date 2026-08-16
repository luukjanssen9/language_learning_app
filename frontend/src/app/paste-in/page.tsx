"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { NewVocabularyRow } from "@/components/vocabulary/NewVocabularyRow";
import { useDecks } from "@/hooks/useDecks";
import { useAddKnownVocabulary, useKnownVocabularyItems } from "@/hooks/useKnownVocabulary";
import { useAnalyzePasteIn, useTranslateUnknownWords } from "@/hooks/usePasteIn";
import { useQuickAddCard } from "@/hooks/useQuickAddCard";
import { useVocabularyItems } from "@/hooks/useVocabulary";
import type { NewVocabularyWord } from "@/lib/api/types";
import { useBootstrapContext } from "@/providers/BootstrapProvider";
import { useCourseContext } from "@/providers/CourseProvider";

export default function PasteInPage() {
  const { userId } = useBootstrapContext();
  const { selectedCourseId } = useCourseContext();
  const searchParams = useSearchParams();
  const { data: decks = [] } = useDecks(userId);
  const { data: vocabItems = [] } = useVocabularyItems(selectedCourseId, userId);
  const { data: knownWords = [] } = useKnownVocabularyItems(selectedCourseId, userId);
  const quickAdd = useQuickAddCard(userId);
  const markKnown = useAddKnownVocabulary();
  const analyze = useAnalyzePasteIn();
  const translate = useTranslateUnknownWords();

  // Lazy initializer, not useState("") + a setter call inside the effect
  // below -- reads the prefill synchronously at first render.
  const [text, setText] = useState(() => searchParams.get("text") ?? "");

  const courseDecks = decks.filter((d) => d.course_id === selectedCourseId);

  async function runAnalyze(textToAnalyze: string) {
    if (!textToAnalyze.trim()) return;
    translate.reset(); // clear any stale glossary from a previous analysis
    const result = await analyze.mutateAsync({
      course_id: selectedCourseId,
      user_id: userId,
      text: textToAnalyze,
    });
    if (result.unknown_words.length > 0) {
      translate.mutate({ course_id: selectedCourseId, words: result.unknown_words });
    }
  }

  function handleAnalyze(e: FormEvent) {
    e.preventDefault();
    void runAnalyze(text);
  }

  // A coverage-panel "Review these words" link arrives here with a
  // pre-filled ?text= (already loaded into `text` via the lazy initializer
  // above) -- run the analysis immediately rather than making the user
  // paste/click again for words we already know are unknown. Deliberately
  // mount-only (not re-run if searchParams changes later): this page is
  // never navigated to itself with a new query, only landed on fresh from
  // elsewhere.
  //
  // Guarded by a ref, not just an empty dependency array: React's
  // StrictMode intentionally double-invokes effects in development, and
  // without this guard that fired two independent analyze+translate call
  // sequences back to back -- found live, not by review, as a real
  // "Couldn't load translations" error from the second, colliding call.
  //
  // The mutateAsync call itself is deferred with setTimeout rather than
  // invoked synchronously in the effect body -- found live, not by review:
  // calling it synchronously here let it start (and its underlying fetch
  // resolve) while StrictMode's dev-only mount -> cleanup -> remount cycle
  // was still unsubscribing/resubscribing this hook's internal mutation
  // observer, and the button got stuck on "Analyzing..." forever even
  // though the request had genuinely succeeded (confirmed via the
  // QueryClient's mutation cache showing "success" while the hook's own
  // `analyze.isPending` never flipped). Deferring past that synchronous
  // double-invoke dance -- which only exists in dev, never in a production
  // build -- avoids the race entirely.
  const hasAutoAnalyzed = useRef(false);
  useEffect(() => {
    if (!searchParams.get("text")) return;
    // The ref isn't flipped until the timer actually fires (not when it's
    // scheduled) -- StrictMode's dev-only mount -> cleanup -> remount cycle
    // clears the first, phantom timer via the cleanup below before it ever
    // runs, so only the second (real, settled) effect instance's timer
    // fires and flips the ref, exactly once.
    const timer = setTimeout(() => {
      if (!hasAutoAnalyzed.current) {
        hasAutoAnalyzed.current = true;
        void runAnalyze(text);
      }
    }, 0);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleAddToDeck(word: NewVocabularyWord, deckId: string) {
    await quickAdd.mutateAsync({
      deck_id: deckId,
      target_text: word.target_text,
      base_text: word.base_text,
      source: "Paste-in",
    });
  }

  async function handleMarkKnown(word: NewVocabularyWord) {
    await markKnown.mutateAsync({
      course_id: selectedCourseId,
      user_id: userId,
      target_text: word.target_text,
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
                  existingKnownWords={knownWords}
                  onAddToDeck={handleAddToDeck}
                  onMarkKnown={handleMarkKnown}
                />
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
