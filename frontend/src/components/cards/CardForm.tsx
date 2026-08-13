"use client";

import { useState, type FormEvent } from "react";
import type { Card, CardDirection } from "@/lib/api/types";

interface CardFormProps {
  initialCard?: Card;
  onSubmit: (values: {
    front_override: string;
    back_override: string;
    direction: CardDirection;
  }) => void;
  onCancel: () => void;
  isSubmitting: boolean;
}

const DIRECTIONS: { value: CardDirection; label: string }[] = [
  { value: "target_to_base", label: "Spanish → English (recognition)" },
  { value: "base_to_target", label: "English → Spanish (production)" },
  { value: "mixed", label: "Mixed" },
];

// front_override/back_override are always literally "shown first" /
// "shown after flip" -- `direction` is stored metadata about which recall
// direction a card is meant to exercise, it never reorders which override
// field renders where. This form's labels explain that to the person
// filling it in; nothing here (or in Flashcard.tsx) branches on direction
// for layout.
export function CardForm({ initialCard, onSubmit, onCancel, isSubmitting }: CardFormProps) {
  const [front, setFront] = useState(initialCard?.front_override ?? "");
  const [back, setBack] = useState(initialCard?.back_override ?? "");
  const [direction, setDirection] = useState<CardDirection>(
    initialCard?.direction ?? "target_to_base",
  );

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit({ front_override: front, back_override: back, direction });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-3 rounded-md border border-line bg-surface p-4"
    >
      <label className="flex flex-col gap-1 text-sm text-ink-soft">
        Front
        <input
          value={front}
          onChange={(e) => setFront(e.target.value)}
          required
          autoFocus
          className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm text-ink-soft">
        Back
        <input
          value={back}
          onChange={(e) => setBack(e.target.value)}
          required
          className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm text-ink-soft">
        Direction
        <select
          value={direction}
          onChange={(e) => setDirection(e.target.value as CardDirection)}
          className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
        >
          {DIRECTIONS.map((d) => (
            <option key={d.value} value={d.value}>
              {d.label}
            </option>
          ))}
        </select>
      </label>
      <div className="flex justify-end gap-2">
        <button type="button" onClick={onCancel} className="px-3 py-1.5 text-sm text-ink-soft">
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-bg disabled:opacity-50"
        >
          {initialCard ? "Save" : "Add card"}
        </button>
      </div>
    </form>
  );
}
