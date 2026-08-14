import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Deck, KnownVocabularyItem } from "@/lib/api/types";
import { KnownVocabularyRow } from "./KnownVocabularyRow";

const deckA: Deck = {
  id: "deck-a",
  user_id: "user-1",
  course_id: "course-1",
  name: "Spanish Vocab",
  description: null,
  daily_new_card_cap: null,
  created_at: "2026-08-14T00:00:00Z",
};

function makeItem(overrides: Partial<KnownVocabularyItem>): KnownVocabularyItem {
  return {
    id: "kv-1",
    course_id: "course-1",
    target_text: "hola",
    source: "manual",
    created_at: "2026-08-14T00:00:00Z",
    ...overrides,
  };
}

describe("KnownVocabularyRow", () => {
  it("renders the word and its source", () => {
    render(
      <KnownVocabularyRow
        item={makeItem({ source: "placement_check" })}
        decks={[deckA]}
        onPromote={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(screen.getByText("hola")).toBeInTheDocument();
    expect(screen.getByText("Placement check")).toBeInTheDocument();
  });

  it("calls onPromote with the item and the only deck", async () => {
    const user = userEvent.setup();
    const onPromote = vi.fn().mockResolvedValue(undefined);
    render(
      <KnownVocabularyRow
        item={makeItem({})}
        decks={[deckA]}
        onPromote={onPromote}
        onDelete={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Promote" }));

    expect(onPromote).toHaveBeenCalledWith(makeItem({}), "deck-a");
  });

  it("hides the promote control once the word is already promoted", () => {
    render(
      <KnownVocabularyRow
        item={makeItem({ source: "promoted" })}
        decks={[deckA]}
        onPromote={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(screen.queryByRole("button", { name: "Promote" })).not.toBeInTheDocument();
    expect(screen.getByText("Promoted")).toBeInTheDocument();
  });

  it("calls onDelete with the item", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn().mockResolvedValue(undefined);
    render(
      <KnownVocabularyRow
        item={makeItem({})}
        decks={[deckA]}
        onPromote={vi.fn()}
        onDelete={onDelete}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Remove" }));

    expect(onDelete).toHaveBeenCalledWith(makeItem({}));
  });

  it("shows a deck picker only when there is more than one deck", () => {
    const deckB: Deck = { ...deckA, id: "deck-b", name: "Extra Deck" };
    const { rerender } = render(
      <KnownVocabularyRow item={makeItem({})} decks={[deckA]} onPromote={vi.fn()} onDelete={vi.fn()} />,
    );
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();

    rerender(
      <KnownVocabularyRow
        item={makeItem({})}
        decks={[deckA, deckB]}
        onPromote={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByRole("combobox")).toBeInTheDocument();
  });
});
