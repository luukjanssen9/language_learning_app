"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useState } from "react";
import { ExerciseCard } from "@/components/lesson/ExerciseCard";
import { IntroScreen } from "@/components/lesson/IntroScreen";
import { useLessonExercises } from "@/hooks/useLessonExercises";
import { useSkills } from "@/hooks/useSkills";
import { useSubmitAttempt } from "@/hooks/useSubmitAttempt";
import { useBootstrapContext } from "@/providers/BootstrapProvider";

function CenteredMessage({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-dvh items-center justify-center p-6 text-center text-ink-soft">
      {children}
    </main>
  );
}

function BackToCourse() {
  return (
    <Link href="/" className="text-sm text-ink-soft underline">
      ← Back to course
    </Link>
  );
}

export default function LessonSessionPage() {
  const { skillId } = useParams<{ skillId: string }>();
  const { userId, courseId } = useBootstrapContext();

  // Reuses the same `skills` query the dashboard already populated (same
  // courseId, same query key) rather than a separate get-by-id fetch --
  // one cache, one source of truth, same convention as the deck detail
  // page reusing the dashboard's `decks` query.
  const { data: skills = [] } = useSkills(courseId);
  const skill = skills.find((s) => s.id === skillId);

  const { data: queue = [], isPending } = useLessonExercises(skillId);
  const submitAttempt = useSubmitAttempt();

  const [introDone, setIntroDone] = useState(false);
  const [index, setIndex] = useState(0);
  const [feedback, setFeedback] = useState<"correct" | "incorrect" | null>(null);
  const [saveError, setSaveError] = useState(false);

  const total = queue.length;
  const currentExercise = queue[index];
  const done = index >= total;

  const handleAnswer = useCallback(
    (submittedAnswer: Record<string, unknown>) => {
      if (!currentExercise) return;
      submitAttempt.mutate(
        {
          exerciseId: currentExercise.id,
          payload: { user_id: userId, submitted_answer: submittedAnswer },
        },
        {
          onSuccess: (data) => setFeedback(data.attempt.is_correct ? "correct" : "incorrect"),
          onError: () => setSaveError(true),
        },
      );
    },
    [currentExercise, submitAttempt, userId],
  );

  const handleContinue = useCallback(() => {
    setFeedback(null);
    setIndex((i) => i + 1);
  }, []);

  if (isPending) return <CenteredMessage>Loading exercises…</CenteredMessage>;
  if (total === 0) {
    return (
      <CenteredMessage>
        <div className="flex flex-col items-center gap-4">
          <p>No exercises in this skill yet.</p>
          <BackToCourse />
        </div>
      </CenteredMessage>
    );
  }

  if (skill?.intro_content && !introDone) {
    return (
      <main className="mx-auto flex min-h-dvh max-w-md flex-col justify-center gap-6 p-4">
        <IntroScreen intro={skill.intro_content} onContinue={() => setIntroDone(true)} />
      </main>
    );
  }

  if (done) {
    return (
      <CenteredMessage>
        <div className="flex flex-col items-center gap-4">
          <p>
            Session complete — {total} exercise{total === 1 ? "" : "s"} practiced.
          </p>
          <BackToCourse />
        </div>
      </CenteredMessage>
    );
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-6 p-4">
      <header className="flex items-center justify-between">
        <Link href="/" className="text-sm text-ink-soft">
          ← Back
        </Link>
        <span className="text-sm text-ink-soft">
          {index + 1} / {total}
        </span>
      </header>

      <div className="h-1 w-full rounded-full bg-line">
        <div
          className="h-full rounded-full bg-accent transition-all"
          style={{ width: `${(index / total) * 100}%` }}
        />
      </div>

      {saveError && (
        <p className="text-center text-xs text-rating-again">
          Couldn&apos;t save the last answer.
        </p>
      )}

      <div className="flex flex-1 flex-col items-center justify-center gap-4">
        {feedback ? (
          <>
            <p
              className={
                feedback === "correct" ? "text-2xl text-rating-good" : "text-2xl text-rating-again"
              }
            >
              {feedback === "correct" ? "Correct!" : "Not quite"}
            </p>
            <button
              type="button"
              onClick={handleContinue}
              className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg"
            >
              Continue
            </button>
          </>
        ) : (
          <ExerciseCard
            exercise={currentExercise}
            onSubmit={handleAnswer}
            disabled={submitAttempt.isPending}
          />
        )}
      </div>
    </main>
  );
}
