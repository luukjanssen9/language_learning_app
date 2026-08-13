"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { cardsApi } from "@/lib/api/cards";
import { queryKeys } from "@/lib/queryKeys";
import type { ReviewRating } from "@/lib/api/types";
import { useDueCards } from "@/hooks/useDueCards";
import { Flashcard } from "@/components/review/Flashcard";
import { RatingButtons } from "@/components/review/RatingButtons";

const KEY_TO_RATING: Record<string, ReviewRating> = {
  "1": "again",
  "2": "hard",
  "3": "good",
  "4": "easy",
};

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

  const { data: queue = [], isPending } = useDueCards(deckId);

  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [saveError, setSaveError] = useState(false);

  const reviewMutation = useMutation({
    mutationFn: ({ cardId, rating }: { cardId: string; rating: ReviewRating }) =>
      cardsApi.review(cardId, rating),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.cards(deckId) }),
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
      // non-blocking banner instead of freezing the session.
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
        <Flashcard card={currentCard} flipped={flipped} onFlip={handleFlip} />
      </div>

      <RatingButtons disabled={!flipped} onRate={handleRate} />
      <p className="text-center text-xs text-ink-soft">1 2 3 4 · space to flip</p>
    </main>
  );
}
