"use client";

import { useRef, useState, type FormEvent } from "react";
import { useCourses } from "@/hooks/useCourses";
import { useDecks } from "@/hooks/useDecks";
import { useLanguages } from "@/hooks/useLanguages";
import { useQuickAddCard } from "@/hooks/useQuickAddCard";
import type { VocabDeckConfig } from "@/lib/api/types";
import { useBootstrapContext } from "@/providers/BootstrapProvider";

// Global and reachable from any page, not scoped to a deck's own page --
// the whole point is capturing a real word mid-shadowing-session, not a
// multi-step "go find the right deck first" flow (2026-08-14 "Anki-style
// vocab decks" decision). A native <dialog> keeps this self-contained
// (focus trapping, Escape-to-close, backdrop) without a UI library.
export function QuickAddButton() {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const { userId } = useBootstrapContext();
  const { data: decks = [] } = useDecks(userId);
  const { data: courses = [] } = useCourses();
  const { data: languages = [] } = useLanguages();
  const quickAdd = useQuickAddCard(userId);

  const [deckId, setDeckId] = useState("");
  const [targetText, setTargetText] = useState("");
  const [baseText, setBaseText] = useState("");
  const [transliteration, setTransliteration] = useState("");
  const [partOfSpeech, setPartOfSpeech] = useState("");
  const [source, setSource] = useState("");
  const [exampleSentence, setExampleSentence] = useState("");
  const [exampleSentenceTranslation, setExampleSentenceTranslation] = useState("");
  const [tags, setTags] = useState("");
  const [justAdded, setJustAdded] = useState(false);

  const selectedDeckId = deckId || decks[0]?.id || "";
  const selectedDeck = decks.find((d) => d.id === selectedDeckId);
  const course = courses.find((c) => c.id === selectedDeck?.course_id);
  const targetLanguage = languages.find((l) => l.id === course?.target_language_id);
  const vocabDeckConfig = targetLanguage?.grammar_config.vocab_deck as VocabDeckConfig | undefined;
  const needsTransliteration = vocabDeckConfig?.needs_transliteration ?? false;

  function resetForm() {
    setTargetText("");
    setBaseText("");
    setTransliteration("");
    setPartOfSpeech("");
    setSource("");
    setExampleSentence("");
    setExampleSentenceTranslation("");
    setTags("");
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selectedDeckId) return;
    quickAdd.mutate(
      {
        deck_id: selectedDeckId,
        target_text: targetText.trim(),
        base_text: baseText.trim(),
        part_of_speech: partOfSpeech.trim() || null,
        source: source.trim() || null,
        example_sentence: exampleSentence.trim() || null,
        example_sentence_translation: exampleSentenceTranslation.trim() || null,
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
        attributes: transliteration.trim() ? { transliteration: transliteration.trim() } : {},
      },
      {
        onSuccess: () => {
          resetForm();
          setJustAdded(true);
          setTimeout(() => setJustAdded(false), 2000);
        },
      },
    );
  }

  // Nowhere to file a note into yet -- the plain "+ Add card" flow on a
  // deck's own page still works for creating the first deck's cards.
  if (decks.length === 0) return null;

  return (
    <>
      <button
        type="button"
        onClick={() => dialogRef.current?.showModal()}
        className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-bg"
      >
        + Quick add
      </button>
      <dialog
        ref={dialogRef}
        // Tailwind's preflight reset strips the browser default `margin:
        // auto` a <dialog> normally centers itself with via showModal() --
        // fixed + inset-0 + m-auto reinstates that centering explicitly
        // (found live: without this the dialog renders pinned to the
        // top-left corner instead of centered).
        className="fixed inset-0 m-auto max-h-[85vh] w-full max-w-md overflow-y-auto rounded-2xl border border-line bg-surface p-6 text-ink backdrop:bg-ink/40"
      >
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-xl text-ink">Quick add a card</h2>
            <button
              type="button"
              onClick={() => dialogRef.current?.close()}
              className="text-sm text-ink-soft"
            >
              Close
            </button>
          </div>

          <label className="flex flex-col gap-1 text-sm text-ink-soft">
            Deck
            <select
              value={selectedDeckId}
              onChange={(e) => setDeckId(e.target.value)}
              className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
            >
              {decks.map((deck) => (
                <option key={deck.id} value={deck.id}>
                  {deck.name}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-sm text-ink-soft">
            Word or phrase
            <input
              value={targetText}
              onChange={(e) => setTargetText(e.target.value)}
              required
              autoFocus
              className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
            />
          </label>

          {needsTransliteration && (
            <label className="flex flex-col gap-1 text-sm text-ink-soft">
              {vocabDeckConfig?.transliteration_label ?? "Transliteration"}
              <input
                value={transliteration}
                onChange={(e) => setTransliteration(e.target.value)}
                className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
              />
            </label>
          )}

          <label className="flex flex-col gap-1 text-sm text-ink-soft">
            Translation
            <input
              value={baseText}
              onChange={(e) => setBaseText(e.target.value)}
              required
              className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
            />
          </label>

          <label className="flex flex-col gap-1 text-sm text-ink-soft">
            Source
            <input
              value={source}
              onChange={(e) => setSource(e.target.value)}
              placeholder="e.g. Movie: Roma"
              className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
            />
          </label>

          <label className="flex flex-col gap-1 text-sm text-ink-soft">
            Example sentence
            <input
              value={exampleSentence}
              onChange={(e) => setExampleSentence(e.target.value)}
              className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
            />
          </label>

          <label className="flex flex-col gap-1 text-sm text-ink-soft">
            Example sentence translation
            <input
              value={exampleSentenceTranslation}
              onChange={(e) => setExampleSentenceTranslation(e.target.value)}
              className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
            />
          </label>

          <label className="flex flex-col gap-1 text-sm text-ink-soft">
            Part of speech
            <input
              value={partOfSpeech}
              onChange={(e) => setPartOfSpeech(e.target.value)}
              className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
            />
          </label>

          <label className="flex flex-col gap-1 text-sm text-ink-soft">
            Tags (comma-separated)
            <input
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              className="rounded-md border border-line bg-bg px-3 py-2 text-ink"
            />
          </label>

          {quickAdd.isError && (
            <p className="text-sm text-rating-again">Couldn&apos;t add this card. Try again.</p>
          )}
          {justAdded && <p className="text-sm text-rating-good">Added.</p>}

          <button
            type="submit"
            disabled={quickAdd.isPending || !selectedDeckId}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg disabled:opacity-50"
          >
            {quickAdd.isPending ? "Adding…" : "Add card"}
          </button>
        </form>
      </dialog>
    </>
  );
}
