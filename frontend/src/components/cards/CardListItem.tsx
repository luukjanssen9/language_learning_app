"use client";

import { useState } from "react";
import type { Card, CardDirection } from "@/lib/api/types";
import { formatCardStatus } from "@/lib/format";
import { CardForm } from "./CardForm";

interface CardListItemProps {
  card: Card;
  onUpdate: (values: {
    front_override: string;
    back_override: string;
    direction: CardDirection;
  }) => void;
  onDelete: () => void;
  isUpdating: boolean;
}

export function CardListItem({ card, onUpdate, onDelete, isUpdating }: CardListItemProps) {
  const [isEditing, setIsEditing] = useState(false);

  // Vocabulary-backed cards (see the 2026-08-14 "Anki-style vocab decks"
  // decision) have no front_override/back_override at all -- resolve from
  // the embedded note instead. Always shown target -> base here regardless
  // of direction: this is an inventory/management list, not the quiz
  // itself, so the canonical note direction reads more naturally than
  // mirroring whichever direction a given card instance tests. A
  // dual-direction note produces two rows for the same words (recognition
  // + production) -- the direction label is what tells them apart.
  const vocab = card.vocabulary_item;
  const frontText = vocab ? vocab.target_text : card.front_override;
  const backText = vocab ? vocab.base_text : card.back_override;
  const directionLabel = vocab
    ? card.direction === "base_to_target"
      ? "Production"
      : "Recognition"
    : null;

  if (isEditing) {
    return (
      <CardForm
        initialCard={card}
        isSubmitting={isUpdating}
        onCancel={() => setIsEditing(false)}
        onSubmit={(values) => {
          onUpdate(values);
          setIsEditing(false);
        }}
      />
    );
  }

  return (
    <div className="flex items-center justify-between gap-4 border border-line bg-surface px-4 py-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-ink">
            {frontText} <span className="text-ink-soft">→</span> {backText}
          </p>
          {/* A prominent pill, not small inline text -- a dual-direction
              note produces two rows with the *same* target/base text
              (recognition + production of one word), which read as an
              accidental duplicate until this distinction is hard to miss
              (found live: reported as "creates a new item" after
              practicing, when it was actually this pre-existing pairing
              becoming visible once the blank-text bug above was fixed). */}
          {directionLabel && (
            <span className="shrink-0 rounded-full border border-line bg-bg px-2 py-0.5 text-xs text-ink-soft">
              {directionLabel}
            </span>
          )}
        </div>
        <p className="mt-0.5 text-xs text-ink-soft">{formatCardStatus(card)}</p>
      </div>
      <div className="flex shrink-0 gap-3 text-sm">
        {/* CardForm only edits front_override/back_override, which a
            vocabulary-backed card doesn't use for display at all
            (Flashcard.tsx always prefers the linked note) -- editing one
            here would silently save without changing anything the
            learner ever sees. Hidden rather than shipped broken; a real
            note editor is a separate, not-yet-built feature. */}
        {!vocab && (
          <button type="button" onClick={() => setIsEditing(true)} className="text-ink-soft">
            Edit
          </button>
        )}
        <button
          type="button"
          onClick={() => {
            if (window.confirm("Delete this card?")) onDelete();
          }}
          className="text-rating-again"
        >
          Delete
        </button>
      </div>
    </div>
  );
}
