import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { VocabularyItem } from "@/lib/api/types";
import { MasteredVocabularyRow } from "./MasteredVocabularyRow";

function makeItem(overrides: Partial<VocabularyItem>): VocabularyItem {
  return {
    id: "v1",
    course_id: "c1",
    user_id: "user-1",
    target_text: "perro",
    base_text: "dog",
    part_of_speech: null,
    attributes: {},
    source: null,
    example_sentence: null,
    example_sentence_translation: null,
    tags: [],
    created_at: "2026-08-15T00:00:00Z",
    ...overrides,
  };
}

describe("MasteredVocabularyRow", () => {
  it("renders the target text, base text, and a Mastered label", () => {
    render(<MasteredVocabularyRow item={makeItem({ target_text: "gato", base_text: "cat" })} />);

    expect(screen.getByText("gato", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("cat", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("Mastered")).toBeInTheDocument();
  });

  it("does not render a Promote or Remove action", () => {
    render(<MasteredVocabularyRow item={makeItem({})} />);

    expect(screen.queryByRole("button", { name: /promote/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /remove/i })).not.toBeInTheDocument();
  });
});
