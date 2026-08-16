"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { cardsApi } from "@/lib/api/cards";
import { queryKeys } from "@/lib/queryKeys";
import type { Card, ReviewRating } from "@/lib/api/types";
import { useCourses } from "@/hooks/useCourses";
import { useDecks } from "@/hooks/useDecks";
import { useDueCards } from "@/hooks/useDueCards";
import { useLanguages } from "@/hooks/useLanguages";
import { Flashcard } from "@/components/review/Flashcard";
import { RatingButtons } from "@/components/review/RatingButtons";
import { useBootstrapContext } from "@/providers/BootstrapProvider";

const KEY_TO_RATING: Record<string, ReviewRating> = {
  "1": "again",
  "2": "hard",
  "3": "good",
  "4": "easy",
};

// A card rated Again/Hard (or a NEW card that doesn't graduate straight to
// Easy) stays in "learning"/"relearning" -- FSRS's short, same-day steps
// (minutes, not days, see PLAN.md's Phase 2 decision log). Real Anki
// resurfaces those within the same sitting instead of only ever moving
// forward; re-inserting a fixed few cards later approximates that without
// building a true due_at-driven interleave scheduler, which is
// disproportionate for a single learner's session size.
const REQUEUE_OFFSET = 3;

function CenteredMessage({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-dvh items-center justify-center p-6 text-center text-ink-soft">
      {children}
    </main>
  );
}

export default function ReviewSessionPage() {
  const { deckId } = useParams<{ deckId: string }>();
  const queryClient = useQueryClient();
  const { userId } = useBootstrapContext();

  const { data: fetchedQueue, isPending } = useDueCards(deckId, userId);

  // A local, mutable copy of the fetched queue -- unlike the frozen fetch
  // itself (staleTime: Infinity, see useDueCards.ts), this needs to grow
  // mid-session when a card gets requeued (see REQUEUE_OFFSET above), so
  // it can't just be the query's own data. Hydrated once, the same
  // "adjust state during render" pattern as the conjugation drill page
  // uses for the same class of problem (deriving local state from query
  // data that may already be cached on first render) -- a lazy useState
  // initializer alone isn't enough since `fetchedQueue` is undefined on
  // that very first render while the query is in flight.
  const [queue, setQueue] = useState<Card[]>([]);
  const [hydratedFrom, setHydratedFrom] = useState<Card[] | null>(null);
  if (fetchedQueue && fetchedQueue !== hydratedFrom) {
    setHydratedFrom(fetchedQueue);
    setQueue(fetchedQueue);
  }

  // Resolved once per session, not per card -- every card in a deck's
  // queue shares the same deck, so the same course/target language.
  // Deliberately NOT read from the course switcher's "currently selected"
  // course (CourseProvider/useCourseContext): a deck belongs to a fixed
  // course regardless of whatever the switcher happens to have selected
  // elsewhere in the app, so using that context here would show the
  // wrong language's transliteration/direction config if the two ever
  // diverge.
  const { data: decks = [] } = useDecks(userId);
  const { data: courses = [] } = useCourses();
  const { data: languages = [] } = useLanguages();
  const deck = decks.find((d) => d.id === deckId);
  const course = courses.find((c) => c.id === deck?.course_id);
  const targetLanguage = languages.find((l) => l.id === course?.target_language_id);

  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [saveError, setSaveError] = useState(false);

  // The review-response callback (fires after a real network round trip)
  // needs whatever `index` is *at that moment*, not whatever it was when
  // handleRate was first called -- the person may have already rated a
  // couple more cards by the time the response lands. Refs can't be
  // written during render (React's rules), so the sync happens in an
  // effect instead -- a legitimate ref-sync use, not the "derive state
  // from props in an effect" anti-pattern this project avoids elsewhere.
  const indexRef = useRef(index);
  useEffect(() => {
    indexRef.current = index;
  }, [index]);

  const reviewMutation = useMutation({
    mutationFn: ({ cardId, rating }: { cardId: string; rating: ReviewRating }) =>
      cardsApi.review(cardId, userId, rating),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.cards(deckId) });
      const updated = data.card;
      const stillLearning = updated.state === "learning" || updated.state === "relearning";
      if (!stillLearning) return;
      setQueue((q) => {
        const insertAt = Math.min(q.length, indexRef.current + 1 + REQUEUE_OFFSET);
        const next = [...q];
        next.splice(insertAt, 0, updated);
        return next;
      });
    },
    onError: () => setSaveError(true),
  });

  const total = queue.length;
  const currentCard = queue[index];
  const done = index >= total;

  const handleFlip = useCallback(() => setFlipped((f) => !f), []);

  const handleRate = useCallback(
    (rating: ReviewRating) => {
      if (!currentCard) return;
      // Optimistic: the rating is already decided by the person; the
      // server call just persists it. Not blocking the UI on the response
      // keeps the review flow snappy -- a failed save surfaces as a small
      // non-blocking banner instead of freezing the session. The requeue
      // (see reviewMutation.onSuccess above) happens once the response
      // actually arrives, since only the server knows the card's new state.
      reviewMutation.mutate({ cardId: currentCard.id, rating });
      setFlipped(false);
      setIndex((i) => i + 1);
    },
    [currentCard, reviewMutation],
  );

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;

      if (e.key === " ") {
        e.preventDefault();
        handleFlip();
      } else if (flipped && e.key in KEY_TO_RATING) {
        handleRate(KEY_TO_RATING[e.key]);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [flipped, handleFlip, handleRate]);

  if (isPending) return <CenteredMessage>Loading due cards…</CenteredMessage>;
  if (total === 0) {
    return (
      <CenteredMessage>
        <div className="flex flex-col items-center gap-4">
          <p>Nothing due in this deck right now.</p>
          <Link href={`/decks/${deckId}`} className="text-sm text-ink-soft underline">
            ← Back to deck
          </Link>
        </div>
      </CenteredMessage>
    );
  }
  if (done) {
    return (
      <CenteredMessage>
        <div className="flex flex-col items-center gap-4">
          <p>
            Session complete — {total} card{total === 1 ? "" : "s"} reviewed.
          </p>
          <Link href={`/decks/${deckId}`} className="text-sm text-ink-soft underline">
            ← Back to deck
          </Link>
        </div>
      </CenteredMessage>
    );
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-6 p-4">
      <header className="flex items-center justify-between">
        <Link href="/" className="text-sm text-ink-soft">
          ← Back
        </Link>
        <span className="text-sm text-ink-soft">
          {index + 1} / {total}
        </span>
      </header>

      <div className="h-1 w-full rounded-full bg-line">
        <div
          className="h-full rounded-full bg-accent transition-all"
          style={{ width: `${(index / total) * 100}%` }}
        />
      </div>

      {saveError && (
        <p className="text-center text-xs text-rating-again">Couldn&apos;t save the last rating.</p>
      )}

      <div className="flex flex-1 items-center justify-center">
        <Flashcard
          card={currentCard}
          flipped={flipped}
          onFlip={handleFlip}
          targetLanguage={targetLanguage}
        />
      </div>

      <RatingButtons disabled={!flipped} onRate={handleRate} />
      <p className="text-center text-xs text-ink-soft">1 2 3 4 · space to flip</p>
    </main>
  );
}
