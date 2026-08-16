import { useQueries } from "@tanstack/react-query";
import { cardsApi } from "@/lib/api/cards";
import type { Deck } from "@/lib/api/types";
import { computeDeckStats, type DeckStats } from "@/lib/deckStats";
import { queryKeys } from "@/lib/queryKeys";

/** One request per deck (`useQueries`), fine at portfolio scale. Follow-up
 * if deck count ever grows: a real backend aggregate (e.g.
 * `GET /decks/stats`) instead of N client-side fetches. Uses the same
 * `queryKeys.cards(deckId)` key as `useCards`, so visiting the dashboard
 * and a deck's detail page within a session shares one cache entry instead
 * of double-fetching. */
export function useDeckStatsList(decks: Deck[]) {
  const results = useQueries({
    queries: decks.map((deck) => ({
      queryKey: queryKeys.cards(deck.id),
      queryFn: () => cardsApi.list(deck.id),
      // Cards don't push updates -- a card scheduled a few minutes out
      // (a short FSRS learning step) silently becomes due while this
      // page just sits open, and nothing else re-renders to notice.
      // Found live: dashboard said "0 due" long after a card actually
      // was, because the fetched card list itself doesn't change just
      // from time passing. Polling is the simple fix for a single-user,
      // local-scale app; revisit if this ever needs to scale further.
      refetchInterval: 30_000,
    })),
  });

  const statsByDeckId = new Map<string, DeckStats>();
  results.forEach((result, i) => {
    if (result.data) statsByDeckId.set(decks[i].id, computeDeckStats(result.data));
  });
  const isLoading = results.some((r) => r.isPending);

  return { statsByDeckId, isLoading };
}
