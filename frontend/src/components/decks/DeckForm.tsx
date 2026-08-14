"use client";

import { useState, type FormEvent } from "react";
import type { Deck } from "@/lib/api/types";

interface DeckFormProps {
  initialDeck?: Deck;
  onSubmit: (values: {
    name: string;
    description: string | null;
    daily_new_card_cap: number | null;
  }) => void;
  onCancel: () => void;
  isSubmitting: boolean;
}

export function DeckForm({ initialDeck, onSubmit, onCancel, isSubmitting }: DeckFormProps) {
  const [name, setName] = useState(initialDeck?.name ?? "");
  const [description, setDescription] = useState(initialDeck?.description ?? "");
  const [dailyNewCardCap, setDailyNewCardCap] = useState(
    initialDeck?.daily_new_card_cap != null ? String(initialDeck.daily_new_card_cap) : "",
  );

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit({
      name: name.trim(),
      description: description.trim() || null,
      daily_new_card_cap: dailyNewCardCap.trim() ? Number(dailyNewCardCap) : null,
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-3 rounded-md border border-line bg-surface p-4"
    >
      <label className="flex flex-col gap-1 text-sm text-ink-soft">
        Name
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          autoFocus
          className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm text-ink-soft">
        Description
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm text-ink-soft">
        Daily new-card cap
        <input
          type="number"
          min={0}
          value={dailyNewCardCap}
          onChange={(e) => setDailyNewCardCap(e.target.value)}
          placeholder="15 (default)"
          className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
        />
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
          Save
        </button>
      </div>
    </form>
  );
}
