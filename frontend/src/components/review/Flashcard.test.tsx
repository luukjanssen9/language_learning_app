import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Card } from "@/lib/api/types";
import { Flashcard } from "./Flashcard";

const card: Card = {
  id: "card-1",
  deck_id: "deck-1",
  vocabulary_item_id: null,
  front_override: "hablar",
  back_override: "to speak",
  direction: "target_to_base",
  created_at: "2026-08-13T00:00:00Z",
  state: "new",
  step: null,
  stability: null,
  difficulty: null,
  due_at: null,
  reps: 0,
  lapses: 0,
  last_reviewed_at: null,
};

describe("Flashcard", () => {
  it("always shows the front text", () => {
    render(<Flashcard card={card} flipped={false} onFlip={() => {}} />);
    expect(screen.getByText("hablar")).toBeInTheDocument();
  });

  it("renders the back text in the DOM only revealed once flipped", () => {
    const { rerender } = render(<Flashcard card={card} flipped={false} onFlip={() => {}} />);
    // The back face is present but visually hidden via backface-visibility
    // (a real 3D flip, not conditional rendering) -- assert on the
    // `flipped` prop driving the rotation class, not DOM presence.
    expect(screen.getByRole("button")).not.toHaveClass("rotate-y-180");

    rerender(<Flashcard card={card} flipped={true} onFlip={() => {}} />);
    expect(screen.getByRole("button")).toHaveClass("rotate-y-180");
    expect(screen.getByText("to speak")).toBeInTheDocument();
  });

  it("calls onFlip when clicked", async () => {
    const onFlip = vi.fn();
    const user = userEvent.setup();
    render(<Flashcard card={card} flipped={false} onFlip={onFlip} />);

    await user.click(screen.getByRole("button"));

    expect(onFlip).toHaveBeenCalledTimes(1);
  });

  it("falls back to a placeholder when front/back text is null", () => {
    render(
      <Flashcard
        card={{ ...card, front_override: null, back_override: null }}
        flipped={false}
        onFlip={() => {}}
      />,
    );
    expect(screen.getByText("(no front text)")).toBeInTheDocument();
  });
});
