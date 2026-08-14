import { describe, expect, it } from "vitest";
import { sortCards } from "./sortCards";
import type { Card, VocabularyItem } from "./api/types";

function makeVocab(overrides: Partial<VocabularyItem>): VocabularyItem {
  return {
    id: "vocab-1",
    course_id: "course-1",
    target_text: "word",
    base_text: "gloss",
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
    front_override: "front",
    back_override: "back",
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

describe("sortCards", () => {
  it("does not mutate the input array", () => {
    const cards = [makeCard({ id: "b", created_at: "2026-08-14T02:00:00Z" }), makeCard({ id: "a", created_at: "2026-08-14T01:00:00Z" })];
    const original = [...cards];
    sortCards(cards, "alphabetical");
    expect(cards).toEqual(original);
  });

  it("orders by created_at ascending for 'created'", () => {
    const cards = [
      makeCard({ id: "b", created_at: "2026-08-14T02:00:00Z" }),
      makeCard({ id: "a", created_at: "2026-08-14T01:00:00Z" }),
    ];
    const sorted = sortCards(cards, "created");
    expect(sorted.map((c) => c.id)).toEqual(["a", "b"]);
  });

  it("orders vocabulary-backed cards alphabetically by target_text", () => {
    const cards = [
      makeCard({ id: "z", vocabulary_item: makeVocab({ target_text: "zebra" }) }),
      makeCard({ id: "a", vocabulary_item: makeVocab({ target_text: "apple" }) }),
    ];
    const sorted = sortCards(cards, "alphabetical");
    expect(sorted.map((c) => c.id)).toEqual(["a", "z"]);
  });

  it("orders override-only cards alphabetically by front_override", () => {
    const cards = [
      makeCard({ id: "z", front_override: "zebra" }),
      makeCard({ id: "a", front_override: "apple" }),
    ];
    const sorted = sortCards(cards, "alphabetical");
    expect(sorted.map((c) => c.id)).toEqual(["a", "z"]);
  });

  it("groups a dual-direction note's recognition and production cards together, recognition first", () => {
    const vocab = makeVocab({ id: "vocab-hello", target_text: "hello" });
    const cards = [
      makeCard({ id: "production", vocabulary_item: vocab, direction: "base_to_target" }),
      makeCard({ id: "other", vocabulary_item: makeVocab({ target_text: "zzz" }) }),
      makeCard({ id: "recognition", vocabulary_item: vocab, direction: "target_to_base" }),
    ];
    const sorted = sortCards(cards, "alphabetical");
    expect(sorted.map((c) => c.id)).toEqual(["recognition", "production", "other"]);
  });

  it("sorts by transliteration when a note has one, not the raw script", () => {
    // Codepoint order for these hanzi would put 谢谢 (xièxie) before 你好
    // (nǐ hǎo) -- pinyin order puts "n" before "x", so getting "你好"
    // first proves the sort key is really the transliteration, not
    // target_text.
    const cards = [
      makeCard({
        id: "xiexie",
        vocabulary_item: makeVocab({
          target_text: "谢谢",
          attributes: { transliteration: "xièxie" },
        }),
      }),
      makeCard({
        id: "nihao",
        vocabulary_item: makeVocab({
          target_text: "你好",
          attributes: { transliteration: "nǐ hǎo" },
        }),
      }),
    ];
    const sorted = sortCards(cards, "alphabetical");
    expect(sorted.map((c) => c.id)).toEqual(["nihao", "xiexie"]);
  });

  it("falls back to target_text when a note has no transliteration", () => {
    const cards = [
      makeCard({ id: "z", vocabulary_item: makeVocab({ target_text: "zebra", attributes: {} }) }),
      makeCard({ id: "a", vocabulary_item: makeVocab({ target_text: "apple", attributes: {} }) }),
    ];
    const sorted = sortCards(cards, "alphabetical");
    expect(sorted.map((c) => c.id)).toEqual(["a", "z"]);
  });

  it("is case-insensitive", () => {
    const cards = [
      makeCard({ id: "upper", vocabulary_item: makeVocab({ target_text: "Banana" }) }),
      makeCard({ id: "lower", vocabulary_item: makeVocab({ target_text: "apple" }) }),
    ];
    const sorted = sortCards(cards, "alphabetical");
    expect(sorted.map((c) => c.id)).toEqual(["lower", "upper"]);
  });
});
