import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { WeakPointsResponse } from "@/lib/api/types";
import { WeakPointsPanel } from "./WeakPointsPanel";

function makeWeakPoints(overrides: Partial<WeakPointsResponse>): WeakPointsResponse {
  return {
    weak_cards: [],
    weak_lesson_words: [],
    weak_skills: [],
    ...overrides,
  };
}

describe("WeakPointsPanel", () => {
  it("renders struggling flashcards with lapse count and a review link", () => {
    const weakPoints = makeWeakPoints({
      weak_cards: [
        {
          vocabulary_item_id: "v1",
          target_text: "gato",
          base_text: "cat",
          deck_id: "d1",
          deck_name: "Spanish deck",
          lapses: 3,
        },
      ],
    });
    render(<WeakPointsPanel weakPoints={weakPoints} />);

    expect(screen.getByText("gato", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("3 lapses")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /gato/ })).toHaveAttribute(
      "href",
      "/decks/d1/review",
    );
  });

  it("uses singular \"lapse\" for a count of 1", () => {
    const weakPoints = makeWeakPoints({
      weak_cards: [
        {
          vocabulary_item_id: "v1",
          target_text: "gato",
          base_text: "cat",
          deck_id: "d1",
          deck_name: "Spanish deck",
          lapses: 1,
        },
      ],
    });
    render(<WeakPointsPanel weakPoints={weakPoints} />);

    expect(screen.getByText("1 lapse")).toBeInTheDocument();
  });

  it("renders struggling lesson words with accuracy and a lesson link", () => {
    const weakPoints = makeWeakPoints({
      weak_lesson_words: [
        {
          vocabulary_item_id: "v2",
          target_text: "malo",
          base_text: "bad",
          skill_id: "s1",
          skill_name: "Vocab Basics",
          accuracy: 0.5,
          times_attempted: 2,
        },
      ],
    });
    render(<WeakPointsPanel weakPoints={weakPoints} />);

    expect(screen.getByText("malo", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("50% accuracy (2 attempts)")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /malo/ })).toHaveAttribute(
      "href",
      "/skills/s1/lesson",
    );
  });

  it("renders skills to revisit with mastery and a lesson link", () => {
    const weakPoints = makeWeakPoints({
      weak_skills: [
        { skill_id: "s2", skill_name: "Shaky Skill", mastery_level: 0.4, times_attempted: 3 },
      ],
    });
    render(<WeakPointsPanel weakPoints={weakPoints} />);

    expect(screen.getByText("Shaky Skill")).toBeInTheDocument();
    expect(screen.getByText("40% mastery")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Shaky Skill" })).toHaveAttribute(
      "href",
      "/skills/s2/lesson",
    );
  });

  it("hides a sub-section with no items", () => {
    const weakPoints = makeWeakPoints({
      weak_skills: [
        { skill_id: "s2", skill_name: "Shaky Skill", mastery_level: 0.4, times_attempted: 3 },
      ],
    });
    render(<WeakPointsPanel weakPoints={weakPoints} />);

    expect(screen.queryByText("Struggling flashcards")).not.toBeInTheDocument();
    expect(screen.queryByText("Struggling words")).not.toBeInTheDocument();
    expect(screen.getByText("Skills to revisit")).toBeInTheDocument();
  });

  it("renders nothing when all three lists are empty", () => {
    const { container } = render(<WeakPointsPanel weakPoints={makeWeakPoints({})} />);

    expect(container).toBeEmptyDOMElement();
  });
});
