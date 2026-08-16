import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Card, Language, VocabularyItem } from "@/lib/api/types";
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
  vocabulary_item: null,
};

const vocabularyItem: VocabularyItem = {
  id: "vocab-1",
  course_id: "course-1",
  user_id: "user-1",
  target_text: "你好",
  base_text: "hello",
  part_of_speech: "word",
  attributes: { transliteration: "nǐ hǎo" },
  source: "Podcast: ChinesePod - Greetings",
  example_sentence: "你好，很高兴认识你。",
  example_sentence_translation: "Hello, nice to meet you.",
  tags: ["greetings"],
  created_at: "2026-08-14T00:00:00Z",
};

const chineseLanguage: Language = {
  id: "lang-1",
  code: "zh",
  name: "Chinese",
  script_direction: "ltr",
  grammar_config: {
    vocab_deck: { dual_direction_cards: true, needs_transliteration: true },
  },
  created_at: "2026-08-14T00:00:00Z",
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

  it("recognition (target_to_base) shows target text + transliteration on the front", () => {
    const recognitionCard: Card = {
      ...card,
      vocabulary_item_id: vocabularyItem.id,
      vocabulary_item: vocabularyItem,
      direction: "target_to_base",
    };
    render(
      <Flashcard
        card={recognitionCard}
        flipped={false}
        onFlip={() => {}}
        targetLanguage={chineseLanguage}
      />,
    );
    expect(screen.getByText("你好 (nǐ hǎo)")).toBeInTheDocument();
    expect(screen.getByText("你好，很高兴认识你。")).toBeInTheDocument();
  });

  it("production (base_to_target) shows base text on the front, target + transliteration on the back", () => {
    const productionCard: Card = {
      ...card,
      vocabulary_item_id: vocabularyItem.id,
      vocabulary_item: vocabularyItem,
      direction: "base_to_target",
    };
    render(
      <Flashcard
        card={productionCard}
        flipped={true}
        onFlip={() => {}}
        targetLanguage={chineseLanguage}
      />,
    );
    expect(screen.getByText("hello")).toBeInTheDocument();
    expect(screen.getByText("你好 (nǐ hǎo)")).toBeInTheDocument();
  });

  it("shows a play-audio button on the target-text face when the language has TTS configured", () => {
    const chineseWithTts: Language = {
      ...chineseLanguage,
      grammar_config: {
        ...chineseLanguage.grammar_config,
        tts: { language_code: "cmn-CN", voice_name: "cmn-CN-Standard-A" },
      },
    };
    const recognitionCard: Card = {
      ...card,
      vocabulary_item_id: vocabularyItem.id,
      vocabulary_item: vocabularyItem,
      direction: "target_to_base",
    };
    render(
      <Flashcard
        card={recognitionCard}
        flipped={false}
        onFlip={() => {}}
        targetLanguage={chineseWithTts}
      />,
    );
    expect(screen.getByRole("button", { name: "Play pronunciation" })).toBeInTheDocument();
  });

  it("hides the play-audio button when the language has no TTS configured", () => {
    const recognitionCard: Card = {
      ...card,
      vocabulary_item_id: vocabularyItem.id,
      vocabulary_item: vocabularyItem,
      direction: "target_to_base",
    };
    render(
      <Flashcard
        card={recognitionCard}
        flipped={false}
        onFlip={() => {}}
        targetLanguage={chineseLanguage}
      />,
    );
    expect(screen.queryByRole("button", { name: "Play pronunciation" })).not.toBeInTheDocument();
  });

  it("hides the play-audio button on the non-target face (production card, front not flipped)", () => {
    const chineseWithTts: Language = {
      ...chineseLanguage,
      grammar_config: {
        ...chineseLanguage.grammar_config,
        tts: { language_code: "cmn-CN", voice_name: "cmn-CN-Standard-A" },
      },
    };
    const productionCard: Card = {
      ...card,
      vocabulary_item_id: vocabularyItem.id,
      vocabulary_item: vocabularyItem,
      direction: "base_to_target",
    };
    // Production card, not flipped -- the front shows base_text, not the
    // target text, so no play button yet.
    render(
      <Flashcard
        card={productionCard}
        flipped={false}
        onFlip={() => {}}
        targetLanguage={chineseWithTts}
      />,
    );
    expect(screen.queryByRole("button", { name: "Play pronunciation" })).not.toBeInTheDocument();
  });

  it("omits transliteration when the target language doesn't need one", () => {
    const spanishLanguage: Language = {
      ...chineseLanguage,
      code: "es",
      name: "Spanish",
      grammar_config: { vocab_deck: { dual_direction_cards: false } },
    };
    const spanishVocab: VocabularyItem = {
      ...vocabularyItem,
      target_text: "hola",
      base_text: "hello",
      attributes: {},
    };
    render(
      <Flashcard
        card={{ ...card, vocabulary_item_id: spanishVocab.id, vocabulary_item: spanishVocab }}
        flipped={false}
        onFlip={() => {}}
        targetLanguage={spanishLanguage}
      />,
    );
    expect(screen.getByText("hola")).toBeInTheDocument();
  });
});
