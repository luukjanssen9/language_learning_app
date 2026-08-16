import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Card, VocabularyItem } from "@/lib/api/types";
import { CardListItem } from "./CardListItem";

function makeVocabItem(overrides: Partial<VocabularyItem>): VocabularyItem {
  return {
    id: "vocab-1",
    course_id: "course-1",
    user_id: "user-1",
    target_text: "perro",
    base_text: "dog",
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

function makeCard(overrides: Partial<Card>): Card {
  return {
    id: "card-1",
    deck_id: "deck-1",
    vocabulary_item_id: null,
    front_override: "hola",
    back_override: "hello",
    direction: "target_to_base",
    created_at: "2026-08-14T00:00:00Z",
    state: "new",
    step: null,
    stability: null,
    difficulty: null,
    due_at: null,
    reps: 0,
    lapses: 0,
    last_reviewed_at: null,
    vocabulary_item: null,
    ...overrides,
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("CardListItem", () => {
  it("renders front/back text for an override-only card, with an Edit button", () => {
    render(
      <CardListItem card={makeCard({})} onUpdate={vi.fn()} onDelete={vi.fn()} isUpdating={false} />,
    );

    expect(screen.getByText("hola", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("hello", { exact: false })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Edit" })).toBeInTheDocument();
  });

  it("resolves front/back text from the linked vocabulary item, with no Edit button", () => {
    const card = makeCard({
      front_override: null,
      back_override: null,
      vocabulary_item_id: "vocab-1",
      vocabulary_item: makeVocabItem({}),
      direction: "target_to_base",
    });
    render(<CardListItem card={card} onUpdate={vi.fn()} onDelete={vi.fn()} isUpdating={false} />);

    expect(screen.getByText("perro", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("dog", { exact: false })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Edit" })).not.toBeInTheDocument();
  });

  it("labels a target_to_base vocabulary card as Recognition", () => {
    const card = makeCard({
      vocabulary_item_id: "vocab-1",
      vocabulary_item: makeVocabItem({}),
      direction: "target_to_base",
    });
    render(<CardListItem card={card} onUpdate={vi.fn()} onDelete={vi.fn()} isUpdating={false} />);

    expect(screen.getByText("Recognition")).toBeInTheDocument();
  });

  it("labels a base_to_target vocabulary card as Production", () => {
    const card = makeCard({
      vocabulary_item_id: "vocab-1",
      vocabulary_item: makeVocabItem({}),
      direction: "base_to_target",
    });
    render(<CardListItem card={card} onUpdate={vi.fn()} onDelete={vi.fn()} isUpdating={false} />);

    expect(screen.getByText("Production")).toBeInTheDocument();
  });

  it("calls onDelete once the confirm dialog is accepted", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const user = userEvent.setup();
    const onDelete = vi.fn();
    render(
      <CardListItem card={makeCard({})} onUpdate={vi.fn()} onDelete={onDelete} isUpdating={false} />,
    );

    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(onDelete).toHaveBeenCalledTimes(1);
  });

  it("does not call onDelete when the confirm dialog is dismissed", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(false);
    const user = userEvent.setup();
    const onDelete = vi.fn();
    render(
      <CardListItem card={makeCard({})} onUpdate={vi.fn()} onDelete={onDelete} isUpdating={false} />,
    );

    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(onDelete).not.toHaveBeenCalled();
  });
});
