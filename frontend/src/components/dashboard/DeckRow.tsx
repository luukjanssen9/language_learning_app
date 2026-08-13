import Link from "next/link";
import type { Deck } from "@/lib/api/types";
import type { DeckStats } from "@/lib/deckStats";

export function DeckRow({ deck, stats }: { deck: Deck; stats: DeckStats | undefined }) {
  const progressPct = Math.round((stats?.progress ?? 0) * 100);

  return (
    <div className="flex items-center justify-between gap-4 border border-line bg-surface p-4">
      <div className="min-w-0 flex-1">
        <Link href={`/decks/${deck.id}`} className="font-display text-lg text-ink">
          {deck.name}
        </Link>
        {deck.description && <p className="mt-0.5 text-sm text-ink-soft">{deck.description}</p>}
        <div className="mt-3 h-1 w-full max-w-48 rounded-full bg-line">
          <div
            className="h-full rounded-full bg-accent transition-all"
            style={{ width: `${progressPct}%` }}
          />
        </div>
        <p className="mt-2 text-xs text-ink-soft">
          {stats ? `${stats.dueCount} due · ${stats.newCount} new` : "Loading…"}
        </p>
      </div>
      <Link
        href={`/decks/${deck.id}/review`}
        className="shrink-0 rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-bg"
      >
        Study
      </Link>
    </div>
  );
}
