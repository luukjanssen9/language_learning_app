import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Deck, JournalEntry, VocabularyItem } from "@/lib/api/types";
import { JournalEntryCard } from "./JournalEntryCard";

const entry: JournalEntry = {
  id: "entry-1",
  user_id: "user-1",
  course_id: "course-1",
  submitted_text: "Ayer voy al mercado.",
  corrected_text: "Ayer fui al mercado.",
  overall_feedback: "Good effort, one tense slip.",
  corrections: [
    {
      original: "ayer voy",
      corrected: "ayer fui",
      explanation: "Past events use the preterite, not the present.",
    },
  ],
  vocabulary_suggestions: [
    {
      target_text: "el mercado",
      base_text: "the market",
      example_sentence: "Fui al mercado por la mañana.",
    },
  ],
  created_at: "2026-08-14T00:00:00Z",
};

const deckA: Deck = {
  id: "deck-a",
  user_id: "user-1",
  course_id: "course-1",
  name: "Spanish Vocab",
  description: null,
  daily_new_card_cap: null,
  created_at: "2026-08-14T00:00:00Z",
};

function vocabItem(overrides: Partial<VocabularyItem>): VocabularyItem {
  return {
    id: "vocab-x",
    course_id: "course-1",
    user_id: "user-1",
    target_text: "placeholder",
    base_text: "placeholder",
    part_of_speech: null,
    attributes: {},
    source: null,
    example_sentence: null,
    example_sentence_translation: null,
    tags: [],
    created_at: "2026-08-14T00:00:00Z",
    ...overrides,
  };
}

describe("JournalEntryCard", () => {
  it("renders the corrected text, feedback, and itemized corrections", () => {
    render(
      <JournalEntryCard
        entry={entry}
        courseDecks={[deckA]}
        existingVocab={[]}
        onAddToDeck={vi.fn()}
      />,
    );

    expect(screen.getByText("Ayer voy al mercado.")).toBeInTheDocument();
    expect(screen.getByText("Ayer fui al mercado.")).toBeInTheDocument();
    expect(screen.getByText("Good effort, one tense slip.")).toBeInTheDocument();
    expect(screen.getByText("ayer voy")).toBeInTheDocument();
    expect(screen.getByText("ayer fui")).toBeInTheDocument();
    expect(
      screen.getByText("Past events use the preterite, not the present."),
    ).toBeInTheDocument();
  });

  it("renders vocabulary suggestions with an add-to-deck button", () => {
    render(
      <JournalEntryCard
        entry={entry}
        courseDecks={[deckA]}
        existingVocab={[]}
        onAddToDeck={vi.fn()}
      />,
    );

    expect(screen.getByText(/el mercado/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "+ Add to deck" })).toBeInTheDocument();
  });

  it("calls onAddToDeck with the suggestion and the only course deck", async () => {
    const user = userEvent.setup();
    const onAddToDeck = vi.fn().mockResolvedValue(undefined);
    render(
      <JournalEntryCard
        entry={entry}
        courseDecks={[deckA]}
        existingVocab={[]}
        onAddToDeck={onAddToDeck}
      />,
    );

    await user.click(screen.getByRole("button", { name: "+ Add to deck" }));

    expect(onAddToDeck).toHaveBeenCalledWith(entry.vocabulary_suggestions[0], "deck-a");
  });

  // Regression test for the real duplicate-vocab bug (2026-08-14): the
  // "Added" state must come from the actual vocabulary list, not local
  // component state that resets to "offered" on every remount/reload --
  // that's exactly what let the same suggestion be accepted twice.
  it("renders as already-added once a matching item exists in the vocabulary list, without any click", () => {
    const existingVocab = [vocabItem({ target_text: "el mercado", base_text: "the market" })];
    render(
      <JournalEntryCard
        entry={entry}
        courseDecks={[deckA]}
        existingVocab={existingVocab}
        onAddToDeck={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Added" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: "+ Add to deck" })).not.toBeInTheDocument();
  });

  it("matches already-added accent- and case-insensitively", () => {
    const existingVocab = [vocabItem({ target_text: "EL MÉRCADO", base_text: "THE MARKET" })];
    render(
      <JournalEntryCard
        entry={entry}
        courseDecks={[deckA]}
        existingVocab={existingVocab}
        onAddToDeck={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Added" })).toBeInTheDocument();
  });

  it("re-renders as Added once the parent passes an updated vocabulary list after a successful add", async () => {
    const user = userEvent.setup();
    const onAddToDeck = vi.fn().mockResolvedValue(undefined);
    const { rerender } = render(
      <JournalEntryCard
        entry={entry}
        courseDecks={[deckA]}
        existingVocab={[]}
        onAddToDeck={onAddToDeck}
      />,
    );

    await user.click(screen.getByRole("button", { name: "+ Add to deck" }));
    // Simulates useQuickAddCard's onSuccess invalidating + refetching the
    // vocabulary-items query that feeds `existingVocab` back in.
    rerender(
      <JournalEntryCard
        entry={entry}
        courseDecks={[deckA]}
        existingVocab={[vocabItem({ target_text: "el mercado", base_text: "the market" })]}
        onAddToDeck={onAddToDeck}
      />,
    );

    expect(screen.getByRole("button", { name: "Added" })).toBeInTheDocument();
  });

  it("does not treat a different sense of the same word (homonym) as already-added", () => {
    // Same target_text, different base_text -- e.g. Dutch "bank" meaning
    // couch vs. bank. Only the couch sense already exists; the financial
    // sense must still show as addable.
    const existingVocab = [vocabItem({ target_text: "el mercado", base_text: "a stall" })];
    render(
      <JournalEntryCard
        entry={entry}
        courseDecks={[deckA]}
        existingVocab={existingVocab}
        onAddToDeck={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "+ Add to deck" })).toBeInTheDocument();
  });

  it("shows a deck picker only when the course has more than one deck", () => {
    const deckB: Deck = { ...deckA, id: "deck-b", name: "Extra Deck" };
    const { rerender } = render(
      <JournalEntryCard
        entry={entry}
        courseDecks={[deckA]}
        existingVocab={[]}
        onAddToDeck={vi.fn()}
      />,
    );
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();

    rerender(
      <JournalEntryCard
        entry={entry}
        courseDecks={[deckA, deckB]}
        existingVocab={[]}
        onAddToDeck={vi.fn()}
      />,
    );
    expect(screen.getByRole("combobox")).toBeInTheDocument();
  });

  it("omits the corrections/vocabulary sections when both are empty", () => {
    const cleanEntry: JournalEntry = {
      ...entry,
      corrections: [],
      vocabulary_suggestions: [],
    };
    render(
      <JournalEntryCard
        entry={cleanEntry}
        courseDecks={[deckA]}
        existingVocab={[]}
        onAddToDeck={vi.fn()}
      />,
    );

    expect(screen.queryByText("Corrections")).not.toBeInTheDocument();
    expect(screen.queryByText("New vocabulary")).not.toBeInTheDocument();
  });
});
