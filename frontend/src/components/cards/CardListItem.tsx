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
        <p className="text-ink">
          {card.front_override} <span className="text-ink-soft">→</span> {card.back_override}
        </p>
        <p className="mt-0.5 text-xs text-ink-soft">{formatCardStatus(card)}</p>
      </div>
      <div className="flex shrink-0 gap-3 text-sm">
        <button type="button" onClick={() => setIsEditing(true)} className="text-ink-soft">
          Edit
        </button>
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
