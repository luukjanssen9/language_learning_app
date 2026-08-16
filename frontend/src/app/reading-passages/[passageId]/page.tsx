"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { NewVocabularyRow } from "@/components/vocabulary/NewVocabularyRow";
import { useDecks } from "@/hooks/useDecks";
import { useAddKnownVocabulary, useKnownVocabularyItems } from "@/hooks/useKnownVocabulary";
import { useQuickAddCard } from "@/hooks/useQuickAddCard";
import { useReadingPassages, useSubmitReadingPassageAttempt } from "@/hooks/useReadingPassages";
import { useVocabularyItems } from "@/hooks/useVocabulary";
import type { NewVocabularyWord } from "@/lib/api/types";
import { useBootstrapContext } from "@/providers/BootstrapProvider";

function CenteredMessage({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-dvh items-center justify-center p-6 text-center text-ink-soft">
      {children}
    </main>
  );
}

// Private, page-local -- same convention as JournalEntryCard.tsx's
// VocabSuggestionRow: not reused elsewhere, so it doesn't need its own
// file. Independently submittable (not a sequential queue like the lesson
// session) -- these are short-answer questions a reader tackles at their
// own pace, not a drilled sequence.
function ComprehensionQuestionCard({
  index,
  questionText,
  onSubmit,
}: {
  index: number;
  questionText: string;
  onSubmit: (answer: string) => Promise<{ is_correct: boolean | null; llm_feedback: string | null }>;
}) {
  const [answer, setAnswer] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{
    is_correct: boolean | null;
    llm_feedback: string | null;
  } | null>(null);

  async function handleSubmit() {
    if (!answer.trim()) return;
    setIsSubmitting(true);
    try {
      setFeedback(await onSubmit(answer.trim()));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-2 border border-line bg-surface p-4">
      <p className="text-ink">
        {index + 1}. {questionText}
      </p>
      <textarea
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        rows={2}
        disabled={isSubmitting}
        className="rounded-md border border-line bg-bg px-3 py-2 text-sm text-ink"
      />
      <button
        type="button"
        onClick={handleSubmit}
        disabled={isSubmitting || !answer.trim()}
        className="self-start rounded-md border border-line px-3 py-1.5 text-xs font-medium text-ink disabled:opacity-50"
      >
        {isSubmitting ? "Grading…" : "Submit"}
      </button>
      {feedback && (
        <p
          className={
            feedback.is_correct ? "text-sm text-rating-good" : "text-sm text-rating-again"
          }
        >
          {feedback.is_correct ? "Correct — " : "Not quite — "}
          {feedback.llm_feedback}
        </p>
      )}
    </div>
  );
}

export default function ReadingPassagePage() {
  const { passageId } = useParams<{ passageId: string }>();
  const { userId, courseId } = useBootstrapContext();

  // Reuses the same reading-passages query the category page already
  // populated (same courseId, same query key) -- same convention as the
  // lesson session page reusing the dashboard's skills query.
  const { data: passages = [], isPending } = useReadingPassages(courseId, userId);
  const passage = passages.find((p) => p.id === passageId);

  const { data: decks = [] } = useDecks();
  const { data: vocabItems = [] } = useVocabularyItems(courseId, userId);
  const { data: knownWords = [] } = useKnownVocabularyItems(courseId, userId);
  const quickAdd = useQuickAddCard();
  const markKnown = useAddKnownVocabulary();
  const submitAttempt = useSubmitReadingPassageAttempt();

  const [showTranslation, setShowTranslation] = useState(false);

  const courseDecks = decks.filter((d) => d.course_id === courseId);

  async function handleAddToDeck(word: NewVocabularyWord, deckId: string) {
    await quickAdd.mutateAsync({
      deck_id: deckId,
      target_text: word.target_text,
      base_text: word.base_text,
      source: "Reading passage",
    });
  }

  async function handleMarkKnown(word: NewVocabularyWord) {
    await markKnown.mutateAsync({
      course_id: courseId,
      user_id: userId,
      target_text: word.target_text,
    });
  }

  async function handleSubmitAnswer(questionIndex: number, submittedAnswer: string) {
    const result = await submitAttempt.mutateAsync({
      passageId: passage!.id,
      payload: { user_id: userId, question_index: questionIndex, submitted_answer: submittedAnswer },
    });
    return { is_correct: result.is_correct, llm_feedback: result.llm_feedback };
  }

  if (isPending) return <CenteredMessage>Loading passage…</CenteredMessage>;
  if (!passage) {
    return (
      <CenteredMessage>
        <div className="flex flex-col items-center gap-4">
          <p>Passage not found.</p>
          <Link href="/course" className="text-sm text-ink-soft underline">
            ← Back to course
          </Link>
        </div>
      </CenteredMessage>
    );
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-6 p-4">
      <Link href="/course" className="text-sm text-ink-soft">
        ← Back to course
      </Link>

      <div className="flex flex-col gap-2">
        <p className="text-lg text-ink">{passage.target_text}</p>
        <button
          type="button"
          onClick={() => setShowTranslation((v) => !v)}
          className="self-start text-xs text-ink-soft underline"
        >
          {showTranslation ? "Hide translation" : "Show translation"}
        </button>
        {showTranslation && <p className="text-sm text-ink-soft">{passage.base_text}</p>}
      </div>

      {passage.new_vocabulary.length > 0 && (
        <div className="flex flex-col gap-2">
          <h3 className="text-xs font-medium uppercase tracking-wide text-ink-soft">
            New vocabulary
          </h3>
          <ul className="flex flex-col gap-2">
            {passage.new_vocabulary.map((word, i) => (
              <NewVocabularyRow
                key={i}
                word={word}
                courseDecks={courseDecks}
                existingVocab={vocabItems}
                existingKnownWords={knownWords}
                onAddToDeck={handleAddToDeck}
                onMarkKnown={handleMarkKnown}
              />
            ))}
          </ul>
        </div>
      )}

      {passage.questions.length > 0 && (
        <div className="flex flex-col gap-3">
          <h3 className="text-xs font-medium uppercase tracking-wide text-ink-soft">
            Comprehension questions
          </h3>
          {passage.questions.map((q, i) => (
            <ComprehensionQuestionCard
              key={i}
              index={i}
              questionText={q.question_text}
              onSubmit={(answer) => handleSubmitAnswer(i, answer)}
            />
          ))}
        </div>
      )}
    </main>
  );
}
