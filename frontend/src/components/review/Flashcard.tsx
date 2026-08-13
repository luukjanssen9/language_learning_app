"use client";

import type { Card } from "@/lib/api/types";

export function Flashcard({
  card,
  flipped,
  onFlip,
}: {
  card: Card;
  flipped: boolean;
  onFlip: () => void;
}) {
  return (
    <div className="mx-auto w-full max-w-sm [perspective:1200px]">
      <button
        type="button"
        onClick={onFlip}
        aria-label={flipped ? "Show word" : "Show answer"}
        className={`relative h-64 w-full transform-3d transition-transform duration-500 ${
          flipped ? "rotate-y-180" : ""
        }`}
      >
        <div className="absolute inset-0 flex items-center justify-center rounded-2xl border border-line bg-surface p-6 backface-hidden">
          {/* card.front_override/back_override are nullable on Card in
              general (a card can be VocabularyItem-linked instead) even
              though this phase's own forms only ever create override-based
              cards -- fall back to a visible placeholder rather than
              rendering blank. */}
          <span className="font-display text-3xl text-ink">
            {card.front_override ?? "(no front text)"}
          </span>
        </div>
        <div className="absolute inset-0 flex rotate-y-180 items-center justify-center rounded-2xl border border-line bg-surface p-6 backface-hidden">
          <span className="text-xl text-ink-soft">{card.back_override ?? "(no back text)"}</span>
        </div>
      </button>
    </div>
  );
}
