"use client";

import { useState, type FormEvent } from "react";
import type { LessonExercise } from "@/lib/api/types";

interface ExerciseCardProps {
  exercise: LessonExercise;
  onSubmit: (submittedAnswer: Record<string, unknown>) => void;
  disabled: boolean;
}

interface TextPromptConfig {
  label: string;
  answerKey: "text" | "answer";
}

// Front is always the question, back is always the correct-answer check --
// `direction`-style metadata doesn't exist for lesson exercises the way it
// does for cards, so there's no branch needed here beyond exercise_type.
function textPromptConfig(exercise: LessonExercise): TextPromptConfig | null {
  switch (exercise.exercise_type) {
    case "translation":
      return { label: `Translate: "${exercise.prompt.source_text}"`, answerKey: "text" };
    case "fill_in_blank":
      return { label: String(exercise.prompt.sentence), answerKey: "text" };
    case "conjugation":
      return {
        label: `Conjugate "${exercise.prompt.infinitive}" (${exercise.prompt.tense}, ${exercise.prompt.mood}, ${exercise.prompt.pronoun})`,
        answerKey: "answer",
      };
    default:
      return null;
  }
}

export function ExerciseCard({ exercise, onSubmit, disabled }: ExerciseCardProps) {
  const [text, setText] = useState("");

  if (exercise.exercise_type === "multiple_choice") {
    const options = exercise.prompt.options as string[];
    return (
      <div className="flex w-full flex-col gap-4">
        <p className="text-center font-display text-xl text-ink">
          {String(exercise.prompt.question)}
        </p>
        <div className="flex flex-col gap-2">
          {options.map((option, index) => (
            <button
              key={option}
              type="button"
              disabled={disabled}
              onClick={() => onSubmit({ selected_index: index })}
              className="rounded-md border border-line bg-surface px-4 py-3 text-left text-ink disabled:opacity-50"
            >
              {option}
            </button>
          ))}
        </div>
      </div>
    );
  }

  const config = textPromptConfig(exercise);
  if (!config) {
    return <p className="text-center text-ink-soft">This exercise type isn&apos;t supported yet.</p>;
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!text.trim() || !config) return;
    onSubmit({ [config.answerKey]: text.trim() });
    setText("");
  }

  return (
    <form onSubmit={handleSubmit} className="flex w-full flex-col gap-4">
      <p className="text-center font-display text-xl text-ink">{config.label}</p>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={disabled}
        autoFocus
        className="rounded-md border border-line bg-bg px-3 py-2 text-center text-ink"
      />
      <button
        type="submit"
        disabled={disabled}
        className="self-center rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg disabled:opacity-50"
      >
        Check
      </button>
    </form>
  );
}
