"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useBulkAddKnownVocabulary } from "@/hooks/useKnownVocabulary";
import { getFrequencyBands } from "@/lib/frequencyBands";
import {
  answerCurrentWord,
  currentWord,
  estimatedKnownBands,
  startPlacementCheck,
  type PlacementCheckState,
} from "@/lib/placementCheck";
import { useBootstrapContext } from "@/providers/BootstrapProvider";
import { useCourseContext } from "@/providers/CourseProvider";

function CenteredMessage({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-dvh items-center justify-center p-6 text-center text-ink-soft">
      {children}
    </main>
  );
}

export default function PlacementCheckPage() {
  const router = useRouter();
  const { userId } = useBootstrapContext();
  const { selectedCourseId, selectedTargetLanguage } = useCourseContext();
  const bulkAdd = useBulkAddKnownVocabulary();

  const bands = selectedTargetLanguage ? getFrequencyBands(selectedTargetLanguage.code) : null;

  // Lazy initializer, not a bare useState(startPlacementCheck(bands)) call
  // -- avoids re-running the (cheap, but still real) setup logic on every
  // render, same convention as this app's other query-independent local
  // state.
  const [state, setState] = useState<PlacementCheckState | null>(() =>
    bands ? startPlacementCheck(bands) : null,
  );

  if (!selectedTargetLanguage || !bands || !state) {
    return (
      <CenteredMessage>
        <div className="flex flex-col items-center gap-4">
          <p>No placement check is available for this language yet.</p>
          <Link href="/known-vocabulary" className="text-sm text-ink-soft underline">
            ← Back
          </Link>
        </div>
      </CenteredMessage>
    );
  }

  const word = currentWord(state);

  function handleAnswer(known: boolean) {
    if (!state) return;
    setState(answerCurrentWord(state, known));
  }

  function handleSave() {
    if (!state) return;
    const words = estimatedKnownBands(state).flatMap((band) => band.words);
    bulkAdd.mutate(
      { course_id: selectedCourseId, user_id: userId, target_texts: words },
      { onSuccess: () => router.push("/known-vocabulary") },
    );
  }

  if (state.done) {
    const knownWordCount = estimatedKnownBands(state).reduce(
      (sum, band) => sum + band.words.length,
      0,
    );
    return (
      <CenteredMessage>
        <div className="flex flex-col items-center gap-4">
          <p>
            Estimated you know around <strong>{knownWordCount}</strong> of the most common{" "}
            {selectedTargetLanguage.name} words.
          </p>
          <button
            type="button"
            onClick={handleSave}
            disabled={bulkAdd.isPending}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg disabled:opacity-50"
          >
            {bulkAdd.isPending ? "Saving…" : "Save to known vocabulary"}
          </button>
          {bulkAdd.isError && (
            <p className="text-sm text-rating-again">Couldn&apos;t save. Try again.</p>
          )}
        </div>
      </CenteredMessage>
    );
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-6 p-4">
      <header className="flex items-center justify-between">
        <Link href="/known-vocabulary" className="text-sm text-ink-soft">
          ← Cancel
        </Link>
        <span className="text-sm text-ink-soft">Question {state.itemsShown + 1}</span>
      </header>

      <div className="flex flex-1 flex-col items-center justify-center gap-6">
        <p className="text-3xl text-ink">{word}</p>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => handleAnswer(false)}
            className="rounded-md border border-line px-4 py-2 text-sm font-medium text-ink"
          >
            I don&apos;t know it
          </button>
          <button
            type="button"
            onClick={() => handleAnswer(true)}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg"
          >
            I know it
          </button>
        </div>
      </div>
    </main>
  );
}
