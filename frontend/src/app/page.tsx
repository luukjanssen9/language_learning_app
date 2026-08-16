"use client";

import { DeckRow } from "@/components/dashboard/DeckRow";
import { NewDeckForm } from "@/components/dashboard/NewDeckForm";
import { WeakPointsPanel } from "@/components/dashboard/WeakPointsPanel";
import { useDeckStatsList } from "@/hooks/useDeckStatsList";
import { useDecks } from "@/hooks/useDecks";
import { useWeakPoints } from "@/hooks/useWeakPoints";
import { useBootstrapContext } from "@/providers/BootstrapProvider";
import { CourseProvider, useCourseContext } from "@/providers/CourseProvider";

// CourseProvider re-instantiated here, not shared from the root layout --
// same convention as journal/vocabulary/course/known-vocabulary/paste-in's
// own layout.tsx files, all reading/writing the same `selectedCourseId`
// localStorage key. The dashboard is the bare `/` route with no
// dedicated route-segment folder to hang a layout.tsx off of, so the
// provider wraps here in page.tsx instead -- only WeakPointsPanel below
// needs it (the deck list itself deliberately spans every course, no
// CourseSwitcher added here for that reason).
export default function DashboardPage() {
  return (
    <CourseProvider>
      <DashboardContent />
    </CourseProvider>
  );
}

function DashboardContent() {
  const { userId } = useBootstrapContext();
  const { data: decks = [], isPending } = useDecks(userId);
  const { statsByDeckId } = useDeckStatsList(decks);
  const { selectedCourseId } = useCourseContext();
  const { data: weakPoints } = useWeakPoints(userId, selectedCourseId);

  const totals = [...statsByDeckId.values()].reduce(
    (acc, s) => ({
      due: acc.due + s.dueCount,
      new: acc.new + s.newCount,
      total: acc.total + s.totalCards,
    }),
    { due: 0, new: 0, total: 0 },
  );

  return (
    <main className="mx-auto flex min-h-dvh max-w-2xl flex-col gap-8 p-6">
      <header>
        <h1 className="font-display text-3xl text-ink">Your decks</h1>
        <p className="mt-1 text-ink-soft">
          {totals.due} due · {totals.new} new · {totals.total} total
        </p>
      </header>

      {weakPoints && <WeakPointsPanel weakPoints={weakPoints} />}

      <section className="flex flex-col gap-3">
        {decks.map((deck) => (
          <DeckRow key={deck.id} deck={deck} stats={statsByDeckId.get(deck.id)} />
        ))}
        {!isPending && decks.length === 0 && (
          <p className="text-ink-soft">No decks yet — add one below to get started.</p>
        )}
      </section>

      <NewDeckForm />
    </main>
  );
}
