import Link from "next/link";
import type { WeakPointsResponse } from "@/lib/api/types";

export function WeakPointsPanel({ weakPoints }: { weakPoints: WeakPointsResponse }) {
  const { weak_cards, weak_lesson_words, weak_skills } = weakPoints;
  if (weak_cards.length === 0 && weak_lesson_words.length === 0 && weak_skills.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-4 border border-line bg-surface p-4">
      <h2 className="text-xs font-medium uppercase tracking-wide text-ink-soft">Weak points</h2>

      {weak_cards.length > 0 && (
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-medium text-ink">Struggling flashcards</h3>
          <ul className="flex flex-col gap-1.5">
            {weak_cards.map((card) => (
              <li
                key={card.vocabulary_item_id}
                className="flex items-center justify-between gap-3 text-sm"
              >
                <Link href={`/decks/${card.deck_id}/review`} className="text-ink underline">
                  {card.target_text} <span className="text-ink-soft">({card.deck_name})</span>
                </Link>
                <span className="text-ink-soft">
                  {card.lapses} {card.lapses === 1 ? "lapse" : "lapses"}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {weak_lesson_words.length > 0 && (
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-medium text-ink">Struggling words</h3>
          <ul className="flex flex-col gap-1.5">
            {weak_lesson_words.map((word) => (
              <li
                key={`${word.vocabulary_item_id}-${word.skill_id}`}
                className="flex items-center justify-between gap-3 text-sm"
              >
                <Link href={`/skills/${word.skill_id}/lesson`} className="text-ink underline">
                  {word.target_text} <span className="text-ink-soft">({word.skill_name})</span>
                </Link>
                <span className="text-ink-soft">
                  {Math.round(word.accuracy * 100)}% accuracy ({word.times_attempted} attempts)
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {weak_skills.length > 0 && (
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-medium text-ink">Skills to revisit</h3>
          <ul className="flex flex-col gap-1.5">
            {weak_skills.map((skill) => (
              <li key={skill.skill_id} className="flex items-center justify-between gap-3 text-sm">
                <Link href={`/skills/${skill.skill_id}/lesson`} className="text-ink underline">
                  {skill.skill_name}
                </Link>
                <span className="text-ink-soft">{Math.round(skill.mastery_level * 100)}% mastery</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
