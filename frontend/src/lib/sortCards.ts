import type { Card } from "./api/types";

export type CardSortOrder = "created" | "alphabetical";

/** The word/phrase a card is inventoried under, for grouping a dual-
 * direction note's recognition/production pair together and for the
 * alphabetical sort key. Prefers `attributes.transliteration` when a note
 * has one (e.g. Chinese pinyin, see the 2026-08-14 "Anki-style vocab
 * decks" decision) -- sorting hanzi by raw code point doesn't read as
 * "alphabetical" the way sorting by its pinyin does; falls back to the
 * target text for every other note, and to the raw front text for
 * override-only cards. A generic attribute-key check, not a per-language
 * branch -- works for any future language that populates the same key. */
function cardSortText(card: Card): string {
  if (card.vocabulary_item) {
    const transliteration = card.vocabulary_item.attributes.transliteration;
    if (typeof transliteration === "string" && transliteration) return transliteration;
    return card.vocabulary_item.target_text;
  }
  return card.front_override ?? "";
}

/** Recognition before production when both exist for the same word --
 * matches the order they're introduced in (recognition is reviewable
 * immediately, production unlocks later), not an arbitrary tiebreak. */
function directionPriority(card: Card): number {
  return card.direction === "base_to_target" ? 1 : 0;
}

/** Pure, independently testable -- same convention as deckStats.ts and
 * format.ts. Always returns a new array; never mutates `cards`. */
export function sortCards(cards: Card[], order: CardSortOrder): Card[] {
  const sorted = [...cards];
  if (order === "alphabetical") {
    sorted.sort((a, b) => {
      const textCompare = cardSortText(a).localeCompare(cardSortText(b), undefined, {
        sensitivity: "base",
      });
      return textCompare !== 0 ? textCompare : directionPriority(a) - directionPriority(b);
    });
  } else {
    sorted.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
  }
  return sorted;
}
