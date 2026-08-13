"use client";

import { useState, type FormEvent } from "react";
import { useBootstrapContext } from "@/providers/BootstrapProvider";
import { useCreateDeck } from "@/hooks/useDecks";

export function NewDeckForm() {
  const { userId, courseId } = useBootstrapContext();
  const createDeck = useCreateDeck();
  const [name, setName] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    createDeck.mutate(
      { user_id: userId, course_id: courseId, name: name.trim() },
      {
        onSuccess: () => {
          setName("");
          setIsOpen(false);
        },
      },
    );
  }

  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="self-start border border-dashed border-line px-4 py-2 text-sm text-ink-soft"
      >
        + New deck
      </button>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2 border border-line bg-surface p-4">
      <label className="flex flex-1 flex-col gap-1 text-sm text-ink-soft">
        Deck name
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          autoFocus
          required
          className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
        />
      </label>
      <button
        type="submit"
        disabled={createDeck.isPending}
        className="rounded-md bg-accent px-3 py-2 text-sm font-medium text-bg disabled:opacity-50"
      >
        Create
      </button>
      <button
        type="button"
        onClick={() => setIsOpen(false)}
        className="px-3 py-2 text-sm text-ink-soft"
      >
        Cancel
      </button>
    </form>
  );
}
