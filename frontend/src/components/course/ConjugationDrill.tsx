"use client";

import { useState } from "react";
import { useSubmitAttempt } from "@/hooks/useSubmitAttempt";
import type { VerbGroup } from "@/lib/practiceCategories";
import { useBootstrapContext } from "@/providers/BootstrapProvider";

// Internal pronoun keys (yo/tú/él/nosotros/vosotros/ellos) match what's
// stored in every seeded exercise's prompt.pronoun -- "usted"/"ustedes"
// are display-only labels for the 3rd-person slots here, since usted/él
// and ustedes/ellos conjugate identically in Spanish. No data changes,
// just friendlier labels for this one component.
const PRONOUN_DISPLAY: { key: string; label: string }[] = [
  { key: "yo", label: "yo" },
  { key: "tú", label: "tú" },
  { key: "él", label: "usted" },
  { key: "nosotros", label: "nosotros" },
  { key: "vosotros", label: "vosotros" },
  { key: "ellos", label: "ustedes" },
];

interface FieldResult {
  isCorrect: boolean;
  correctAnswer: string | null;
}

export function ConjugationDrill({
  verbGroup,
  onTryAnother,
}: {
  verbGroup: VerbGroup;
  onTryAnother: () => void;
}) {
  const { userId } = useBootstrapContext();
  const submitAttempt = useSubmitAttempt();

  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [results, setResults] = useState<Record<string, FieldResult> | null>(null);

  const allFilled = PRONOUN_DISPLAY.every(({ key }) => (answers[key] ?? "").trim().length > 0);
  const hasWrongField = results ? Object.values(results).some((r) => !r.isCorrect) : false;

  // Reused for both the first check and every recheck -- re-submitting an
  // already-correct field is harmless (it just grades correct again), so
  // there's no need for a separate "only resubmit the wrong ones" path.
  async function handleCheck() {
    const entries = await Promise.all(
      PRONOUN_DISPLAY.map(async ({ key }) => {
        const exercise = verbGroup.exercisesByPronoun[key];
        const answer = (answers[key] ?? "").trim();
        const data = await submitAttempt.mutateAsync({
          exerciseId: exercise.id,
          payload: { user_id: userId, submitted_answer: { answer } },
        });
        return [
          key,
          { isCorrect: data.attempt.is_correct === true, correctAnswer: data.correct_answer },
        ] as const;
      }),
    );
    setResults(Object.fromEntries(entries));
  }

  const correctCount = results ? Object.values(results).filter((r) => r.isCorrect).length : 0;

  return (
    <div className="flex flex-col gap-4">
      <p className="text-center font-display text-2xl text-ink">{verbGroup.infinitive}</p>

      <div className="flex flex-col gap-2">
        {PRONOUN_DISPLAY.map(({ key, label }) => {
          const result = results?.[key];
          // Correct fields lock once graded (nothing to fix); wrong ones
          // stay editable so a mistake can be corrected in place rather
          // than forcing a whole new verb.
          const locked = result?.isCorrect === true;
          return (
            <div key={key} className="flex flex-col gap-1">
              <label className="flex items-center gap-3">
                <span className="w-24 shrink-0 text-sm text-ink-soft">{label}</span>
                <input
                  value={answers[key] ?? ""}
                  onChange={(e) => setAnswers((a) => ({ ...a, [key]: e.target.value }))}
                  disabled={locked || submitAttempt.isPending}
                  className="flex-1 rounded-md border border-line bg-bg px-3 py-2 text-ink disabled:opacity-70"
                />
                {result && (
                  <span
                    className={result.isCorrect ? "w-4 text-rating-good" : "w-4 text-rating-again"}
                  >
                    {result.isCorrect ? "✓" : "✗"}
                  </span>
                )}
              </label>
              {result && !result.isCorrect && result.correctAnswer && (
                <p className="pl-[6.75rem] text-xs text-ink-soft">
                  Correct: <span className="text-ink">{result.correctAnswer}</span>
                </p>
              )}
            </div>
          );
        })}
      </div>

      {results && <p className="text-center text-ink">{correctCount}/6 correct</p>}

      <div className="flex justify-center gap-3">
        {(!results || hasWrongField) && (
          <button
            type="button"
            onClick={handleCheck}
            disabled={!allFilled || submitAttempt.isPending}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg disabled:opacity-50"
          >
            {results ? "Recheck" : "Check all"}
          </button>
        )}
        {results && (
          <button
            type="button"
            onClick={onTryAnother}
            className="rounded-md border border-line px-4 py-2 text-sm font-medium text-ink"
          >
            Try another verb
          </button>
        )}
      </div>
    </div>
  );
}
