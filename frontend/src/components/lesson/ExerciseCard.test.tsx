import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { LessonExercise } from "@/lib/api/types";
import { ExerciseCard } from "./ExerciseCard";

const baseExercise: LessonExercise = {
  id: "ex-1",
  skill_id: "skill-1",
  exercise_type: "free_text",
  prompt: {},
  order_index: 0,
  specialty_module: null,
  created_at: "2026-08-14T00:00:00Z",
};

describe("ExerciseCard - free_text", () => {
  it("renders a translate label and a textarea for the source_text prompt shape", () => {
    const exercise: LessonExercise = {
      ...baseExercise,
      prompt: { source_text: "Thank you very much for your help." },
    };
    render(<ExerciseCard exercise={exercise} onSubmit={() => {}} disabled={false} />);

    expect(
      screen.getByText('Translate: "Thank you very much for your help."'),
    ).toBeInTheDocument();
    expect(screen.getByRole("textbox").tagName).toBe("TEXTAREA");
  });

  it("renders the question text and a textarea for the question_text prompt shape", () => {
    const exercise: LessonExercise = {
      ...baseExercise,
      prompt: { question_text: "¿Cómo te llamas?" },
    };
    render(<ExerciseCard exercise={exercise} onSubmit={() => {}} disabled={false} />);

    expect(screen.getByText("¿Cómo te llamas?")).toBeInTheDocument();
    expect(screen.getByRole("textbox").tagName).toBe("TEXTAREA");
  });

  it("submits the typed answer under the text key", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const exercise: LessonExercise = {
      ...baseExercise,
      prompt: { question_text: "¿Cómo te llamas?" },
    };
    render(<ExerciseCard exercise={exercise} onSubmit={onSubmit} disabled={false} />);

    await user.type(screen.getByRole("textbox"), "Me llamo Luuk.");
    await user.click(screen.getByRole("button", { name: "Check" }));

    expect(onSubmit).toHaveBeenCalledWith({ text: "Me llamo Luuk." });
  });

  it("shows 'Grading…' instead of 'Check' while a free_text submission is pending", () => {
    const exercise: LessonExercise = {
      ...baseExercise,
      prompt: { question_text: "¿Cómo te llamas?" },
    };
    render(<ExerciseCard exercise={exercise} onSubmit={() => {}} disabled={true} />);

    expect(screen.getByRole("button", { name: "Grading…" })).toBeInTheDocument();
  });

  it("uses a single-line input (not a textarea) for translation exercises", () => {
    const exercise: LessonExercise = {
      ...baseExercise,
      exercise_type: "translation",
      prompt: { source_text: "hello", correct_answer: "hola" },
    };
    render(<ExerciseCard exercise={exercise} onSubmit={() => {}} disabled={false} />);

    expect(screen.getByRole("textbox").tagName).toBe("INPUT");
    expect(screen.getByRole("button", { name: "Check" })).toBeInTheDocument();
  });
});
