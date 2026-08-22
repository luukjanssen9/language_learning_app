"use client";

import { useRef, useState, type FormEvent } from "react";
import { useGenerateCard } from "@/hooks/useGenerateCard";

interface GenerateCardButtonProps {
  deckId: string;
}

// Companion to CardForm's manual "+ Add card" flow: instead of typing
// both sides of the note by hand, the learner types one word in the
// course's base language and an LLM call (POST /cards/generate) fills in
// the target-language translation, part of speech, and an example
// sentence -- see app/services/card_generation.py. Scoped to this deck's
// own page (unlike the global QuickAddButton dialog) since the deck --
// and therefore the target language -- is already fixed by context here.
export function GenerateCardButton({ deckId }: GenerateCardButtonProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const generateCard = useGenerateCard();
  const [word, setWord] = useState("");
  const [lastGenerated, setLastGenerated] = useState<{
    target_text: string;
    base_text: string;
  } | null>(null);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = word.trim();
    if (!trimmed) return;
    generateCard.mutate(
      { deck_id: deckId, base_text: trimmed },
      {
        onSuccess: (data) => {
          setLastGenerated({
            target_text: data.vocabulary_item.target_text,
            base_text: data.vocabulary_item.base_text,
          });
          setWord("");
        },
      },
    );
  }

  return (
    <>
      <button
        type="button"
        onClick={() => {
          setLastGenerated(null);
          generateCard.reset();
          dialogRef.current?.showModal();
        }}
        className="self-start rounded-md border border-line px-4 py-2 text-sm text-ink-soft"
      >
        + Generate with AI
      </button>
      <dialog
        ref={dialogRef}
        // See QuickAddButton.tsx for why the fixed/inset-0/m-auto trio is
        // needed to center a <dialog> under Tailwind's preflight reset.
        className="fixed inset-0 m-auto max-h-[85vh] w-full max-w-sm overflow-y-auto rounded-2xl border border-line bg-surface p-6 text-ink backdrop:bg-ink/40"
      >
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-xl text-ink">Generate a flashcard</h2>
            <button
              type="button"
              onClick={() => dialogRef.current?.close()}
              className="text-sm text-ink-soft"
            >
              Close
            </button>
          </div>

          <label className="flex flex-col gap-1 text-sm text-ink-soft">
            Word or phrase
            <input
              value={word}
              onChange={(e) => setWord(e.target.value)}
              required
              autoFocus
              placeholder="e.g. breakfast"
              className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
            />
          </label>

          {generateCard.isError && (
            <p className="text-sm text-rating-again">Couldn&apos;t generate a card. Try again.</p>
          )}
          {lastGenerated && (
            <p className="text-sm text-rating-good">
              Added: {lastGenerated.target_text} → {lastGenerated.base_text}
            </p>
          )}

          <button
            type="submit"
            disabled={generateCard.isPending || !word.trim()}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg disabled:opacity-50"
          >
            {generateCard.isPending ? "Generating…" : "Generate flashcard"}
          </button>
        </form>
      </dialog>
    </>
  );
}
