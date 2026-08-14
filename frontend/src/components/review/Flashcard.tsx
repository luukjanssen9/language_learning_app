"use client";

import { PlayAudioButton } from "@/components/audio/PlayAudioButton";
import type { Card, Language, VocabDeckConfig } from "@/lib/api/types";

function sideContent(
  card: Card,
  targetLanguage: Language | undefined,
): { front: string; frontSub: string | null; back: string; backSub: string | null } {
  const vocab = card.vocabulary_item;
  if (!vocab) {
    // card.front_override/back_override are nullable on Card in general
    // (a card can be VocabularyItem-linked instead) even though Phase 3's
    // own forms only ever create override-based cards -- fall back to a
    // visible placeholder rather than rendering blank.
    return {
      front: card.front_override ?? "(no front text)",
      frontSub: null,
      back: card.back_override ?? "(no back text)",
      backSub: null,
    };
  }

  const vocabDeckConfig = targetLanguage?.grammar_config.vocab_deck as VocabDeckConfig | undefined;
  const transliteration = vocabDeckConfig?.needs_transliteration
    ? (vocab.attributes.transliteration as string | undefined)
    : undefined;
  const targetDisplay = transliteration ? `${vocab.target_text} (${transliteration})` : vocab.target_text;

  // Direction genuinely drives layout for vocabulary-backed cards, unlike
  // override-based cards above (direction is stored metadata there,
  // never affecting which override renders where) -- production
  // (base_to_target) cards test recall from meaning alone, so the base
  // text has to come first, not the target text (2026-08-14 "Anki-style
  // vocab decks" decision).
  if (card.direction === "base_to_target") {
    return {
      front: vocab.base_text,
      frontSub: vocab.example_sentence_translation,
      back: targetDisplay,
      backSub: vocab.example_sentence,
    };
  }
  return {
    front: targetDisplay,
    frontSub: vocab.example_sentence,
    back: vocab.base_text,
    backSub: vocab.example_sentence_translation,
  };
}

export function Flashcard({
  card,
  flipped,
  onFlip,
  targetLanguage,
}: {
  card: Card;
  flipped: boolean;
  onFlip: () => void;
  targetLanguage?: Language;
}) {
  const { front, frontSub, back, backSub } = sideContent(card, targetLanguage);

  // Shown only on whichever face currently displays the target text --
  // front for recognition cards, back for production cards (the same
  // direction check sideContent makes) -- and only once that face is
  // actually the one showing, not just present in the DOM (both faces
  // always are, per the 3D-flip approach below). A sibling overlay, not
  // nested inside the flip <button>: a <button> inside a <button> is
  // invalid HTML, and it would also fire onFlip via event bubbling.
  const vocab = card.vocabulary_item;
  const hasTts = Boolean(targetLanguage?.grammar_config.tts);
  const targetSide: "front" | "back" = card.direction === "base_to_target" ? "back" : "front";
  const isShowingTargetSide = flipped ? targetSide === "back" : targetSide === "front";
  const showPlayButton = vocab && hasTts && isShowingTargetSide;

  return (
    <div className="relative mx-auto w-full max-w-sm [perspective:1200px]">
      <button
        type="button"
        onClick={onFlip}
        aria-label={flipped ? "Show word" : "Show answer"}
        className={`relative h-64 w-full transform-3d transition-transform duration-500 ${
          flipped ? "rotate-y-180" : ""
        }`}
      >
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 rounded-2xl border border-line bg-surface p-6 backface-hidden">
          <span className="font-display text-3xl text-ink">{front}</span>
          {frontSub && <span className="text-center text-sm text-ink-soft">{frontSub}</span>}
        </div>
        <div className="absolute inset-0 flex rotate-y-180 flex-col items-center justify-center gap-3 rounded-2xl border border-line bg-surface p-6 backface-hidden">
          <span className="text-xl text-ink-soft">{back}</span>
          {backSub && <span className="text-center text-sm text-ink-soft">{backSub}</span>}
        </div>
      </button>
      {showPlayButton && (
        <div className="absolute right-4 top-4 z-10">
          <PlayAudioButton vocabularyItemId={vocab.id} />
        </div>
      )}
    </div>
  );
}
