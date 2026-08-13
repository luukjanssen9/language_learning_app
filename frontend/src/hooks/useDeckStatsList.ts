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
    })),
  });

  const statsByDeckId = new Map<string, DeckStats>();
  results.forEach((result, i) => {
    if (result.data) statsByDeckId.set(decks[i].id, computeDeckStats(result.data));
  });
  const isLoading = results.some((r) => r.isPending);

  return { statsByDeckId, isLoading };
}
