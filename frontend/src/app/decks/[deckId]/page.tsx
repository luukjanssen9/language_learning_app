"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { CardForm } from "@/components/cards/CardForm";
import { CardListItem } from "@/components/cards/CardListItem";
import { GenerateCardButton } from "@/components/cards/GenerateCardButton";
import { DeckForm } from "@/components/decks/DeckForm";
import { useCards, useCreateCard, useDeleteCard, useUpdateCard } from "@/hooks/useCards";
import { useDecks, useDeleteDeck, useUpdateDeck } from "@/hooks/useDecks";
import { sortCards, type CardSortOrder } from "@/lib/sortCards";

const SORT_OPTIONS: { value: CardSortOrder; label: string }[] = [
  { value: "created", label: "Recently added" },
  { value: "alphabetical", label: "Alphabetical" },
];

export default function DeckDetailPage() {
  // useParams(), not the `params` prop: `params` is a Promise in server
  // components as of Next 15+, and this page has no server-side data
  // fetching to justify becoming one -- useParams() is the client-safe way
  // to read the dynamic segment.
  const { deckId } = useParams<{ deckId: string }>();
  const router = useRouter();
  const [isAdding, setIsAdding] = useState(false);
  const [isEditingDeck, setIsEditingDeck] = useState(false);
  const [sortOrder, setSortOrder] = useState<CardSortOrder>("created");

  // Reuses the same `decks` query the dashboard already populated, rather
  // than a separate get-by-id fetch -- one cache, one source of truth.
  const { data: decks = [] } = useDecks();
  const deck = decks.find((d) => d.id === deckId);
  const updateDeck = useUpdateDeck();
  const deleteDeck = useDeleteDeck();

  const { data: cards = [], isPending } = useCards(deckId);
  const createCard = useCreateCard(deckId);
  const updateCard = useUpdateCard(deckId);
  const deleteCard = useDeleteCard(deckId);
  const sortedCards = sortCards(cards, sortOrder);

  return (
    <main className="mx-auto flex min-h-dvh max-w-2xl flex-col gap-6 p-6">
      <div>
        <Link href="/" className="text-sm text-ink-soft">
          ← Back
        </Link>
        {isEditingDeck && deck ? (
          <div className="mt-2">
            <DeckForm
              initialDeck={deck}
              isSubmitting={updateDeck.isPending}
              onCancel={() => setIsEditingDeck(false)}
              onSubmit={(values) => {
                updateDeck.mutate(
                  { id: deckId, payload: values },
                  { onSuccess: () => setIsEditingDeck(false) },
                );
              }}
            />
          </div>
        ) : (
          <div className="mt-2 flex items-start justify-between gap-4">
            <div>
              <h1 className="font-display text-3xl text-ink">{deck?.name ?? "Deck"}</h1>
              {deck?.description && <p className="mt-1 text-ink-soft">{deck.description}</p>}
            </div>
            <div className="flex shrink-0 gap-3 pt-1 text-sm">
              <button
                type="button"
                onClick={() => setIsEditingDeck(true)}
                className="text-ink-soft"
              >
                Edit
              </button>
              <button
                type="button"
                onClick={() => {
                  if (window.confirm("Delete this deck and all its cards?")) {
                    deleteDeck.mutate(deckId, { onSuccess: () => router.push("/") });
                  }
                }}
                className="text-rating-again"
              >
                Delete
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between gap-4">
        <Link
          href={`/decks/${deckId}/review`}
          className="self-start rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg"
        >
          Start review
        </Link>
        {cards.length > 0 && (
          <label className="flex items-center gap-2 text-sm text-ink-soft">
            Sort
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value as CardSortOrder)}
              className="rounded-md border border-line bg-bg px-2 py-1 text-ink"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      <section className="flex flex-col gap-3">
        {sortedCards.map((card) => (
          <CardListItem
            key={card.id}
            card={card}
            isUpdating={updateCard.isPending}
            onUpdate={(values) => updateCard.mutate({ id: card.id, payload: values })}
            onDelete={() => deleteCard.mutate(card.id)}
          />
        ))}
        {!isPending && cards.length === 0 && (
          <p className="text-ink-soft">No cards yet — add one below.</p>
        )}
      </section>

      {isAdding ? (
        <CardForm
          isSubmitting={createCard.isPending}
          onCancel={() => setIsAdding(false)}
          onSubmit={(values) => {
            createCard.mutate({ deck_id: deckId, ...values }, { onSuccess: () => setIsAdding(false) });
          }}
        />
      ) : (
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => setIsAdding(true)}
            className="self-start border border-dashed border-line px-4 py-2 text-sm text-ink-soft"
          >
            + Add card
          </button>
          <GenerateCardButton deckId={deckId} />
        </div>
      )}
    </main>
  );
}
