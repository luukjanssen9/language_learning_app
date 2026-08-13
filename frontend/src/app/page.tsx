"use client";

import { DeckRow } from "@/components/dashboard/DeckRow";
import { NewDeckForm } from "@/components/dashboard/NewDeckForm";
import { useDeckStatsList } from "@/hooks/useDeckStatsList";
import { useDecks } from "@/hooks/useDecks";

export default function DashboardPage() {
  const { data: decks = [], isPending } = useDecks();
  const { statsByDeckId } = useDeckStatsList(decks);

  const totals = [...statsByDeckId.values()].reduce(
    (acc, s) => ({ due: acc.due + s.dueCount, new: acc.new + s.newCount }),
    { due: 0, new: 0 },
  );

  return (
    <main className="mx-auto flex min-h-dvh max-w-2xl flex-col gap-8 p-6">
      <header>
        <h1 className="font-display text-3xl text-ink">Your decks</h1>
        <p className="mt-1 text-ink-soft">
          {totals.due} due · {totals.new} new
        </p>
      </header>

      <section className="flex flex-col gap-3">
        {decks.map((deck) => (
          <DeckRow key={deck.id} deck={deck} stats={statsByDeckId.get(deck.id)} />
        ))}
        {!isPending && decks.length === 0 && (
          <p className="text-ink-soft">No decks yet — add one below to get started.</p>
        )}
      </section>

      <NewDeckForm />

      {/* Phase 4's lesson path slots in here as a sibling section, per the
          2026-08-13 Unified Dashboard decision -- deliberately no stub
          built now. */}
    </main>
  );
}
