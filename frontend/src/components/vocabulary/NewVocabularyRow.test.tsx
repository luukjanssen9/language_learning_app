import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Deck, KnownVocabularyItem, NewVocabularyWord, VocabularyItem } from "@/lib/api/types";
import { NewVocabularyRow } from "./NewVocabularyRow";

const word: NewVocabularyWord = { target_text: "el mercado", base_text: "the market" };

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

function knownItem(overrides: Partial<KnownVocabularyItem>): KnownVocabularyItem {
  return {
    id: "known-x",
    course_id: "course-1",
    user_id: "user-1",
    target_text: "placeholder",
    source: "manual",
    created_at: "2026-08-14T00:00:00Z",
    ...overrides,
  };
}

describe("NewVocabularyRow", () => {
  it("renders the word and its translation", () => {
    render(
      <NewVocabularyRow
        word={word}
        courseDecks={[deckA]}
        existingVocab={[]}
        existingKnownWords={[]}
        onAddToDeck={vi.fn()}
        onMarkKnown={vi.fn()}
      />,
    );

    expect(screen.getByText(/el mercado/)).toBeInTheDocument();
    expect(screen.getByText(/the market/)).toBeInTheDocument();
  });

  it("calls onAddToDeck with the word and the only course deck", async () => {
    const user = userEvent.setup();
    const onAddToDeck = vi.fn().mockResolvedValue(undefined);
    render(
      <NewVocabularyRow
        word={word}
        courseDecks={[deckA]}
        existingVocab={[]}
        existingKnownWords={[]}
        onAddToDeck={onAddToDeck}
        onMarkKnown={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "+ Add to deck" }));

    expect(onAddToDeck).toHaveBeenCalledWith(word, "deck-a");
  });

  it("renders as already-added once a matching item exists in the vocabulary list", () => {
    const existingVocab = [vocabItem({ target_text: "el mercado", base_text: "the market" })];
    render(
      <NewVocabularyRow
        word={word}
        courseDecks={[deckA]}
        existingVocab={existingVocab}
        existingKnownWords={[]}
        onAddToDeck={vi.fn()}
        onMarkKnown={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Added" })).toBeDisabled();
  });

  it("matches already-added accent- and case-insensitively", () => {
    const existingVocab = [vocabItem({ target_text: "EL MÉRCADO", base_text: "THE MARKET" })];
    render(
      <NewVocabularyRow
        word={word}
        courseDecks={[deckA]}
        existingVocab={existingVocab}
        existingKnownWords={[]}
        onAddToDeck={vi.fn()}
        onMarkKnown={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Added" })).toBeInTheDocument();
  });

  it("does not treat a different sense of the same word (homonym) as already-added", () => {
    const existingVocab = [vocabItem({ target_text: "el mercado", base_text: "a stall" })];
    render(
      <NewVocabularyRow
        word={word}
        courseDecks={[deckA]}
        existingVocab={existingVocab}
        existingKnownWords={[]}
        onAddToDeck={vi.fn()}
        onMarkKnown={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "+ Add to deck" })).toBeInTheDocument();
  });

  it("re-renders as Added once the parent passes an updated vocabulary list after a successful add", async () => {
    const user = userEvent.setup();
    const onAddToDeck = vi.fn().mockResolvedValue(undefined);
    const { rerender } = render(
      <NewVocabularyRow
        word={word}
        courseDecks={[deckA]}
        existingVocab={[]}
        existingKnownWords={[]}
        onAddToDeck={onAddToDeck}
        onMarkKnown={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "+ Add to deck" }));
    rerender(
      <NewVocabularyRow
        word={word}
        courseDecks={[deckA]}
        existingVocab={[vocabItem({ target_text: "el mercado", base_text: "the market" })]}
        existingKnownWords={[]}
        onAddToDeck={onAddToDeck}
        onMarkKnown={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Added" })).toBeInTheDocument();
  });

  it("calls onMarkKnown with the word", async () => {
    const user = userEvent.setup();
    const onMarkKnown = vi.fn().mockResolvedValue(undefined);
    render(
      <NewVocabularyRow
        word={word}
        courseDecks={[deckA]}
        existingVocab={[]}
        existingKnownWords={[]}
        onAddToDeck={vi.fn()}
        onMarkKnown={onMarkKnown}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Mark as known" }));

    expect(onMarkKnown).toHaveBeenCalledWith(word);
  });

  it("renders as already-known once a matching item exists in the known-words list", () => {
    const existingKnownWords = [knownItem({ target_text: "el mercado" })];
    render(
      <NewVocabularyRow
        word={word}
        courseDecks={[deckA]}
        existingVocab={[]}
        existingKnownWords={existingKnownWords}
        onAddToDeck={vi.fn()}
        onMarkKnown={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Known" })).toBeDisabled();
  });

  it("matches already-known accent- and case-insensitively", () => {
    const existingKnownWords = [knownItem({ target_text: "EL MÉRCADO" })];
    render(
      <NewVocabularyRow
        word={word}
        courseDecks={[deckA]}
        existingVocab={[]}
        existingKnownWords={existingKnownWords}
        onAddToDeck={vi.fn()}
        onMarkKnown={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Known" })).toBeInTheDocument();
  });

  it("adding to a deck and marking known are independent", () => {
    const existingVocab = [vocabItem({ target_text: "el mercado", base_text: "the market" })];
    render(
      <NewVocabularyRow
        word={word}
        courseDecks={[deckA]}
        existingVocab={existingVocab}
        existingKnownWords={[]}
        onAddToDeck={vi.fn()}
        onMarkKnown={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Added" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Mark as known" })).not.toBeDisabled();
  });
});
