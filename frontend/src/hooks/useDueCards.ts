import { useQuery } from "@tanstack/react-query";
import { cardsApi } from "@/lib/api/cards";
import { queryKeys } from "@/lib/queryKeys";

/** Fetched once and frozen for the session (`staleTime: Infinity`) -- a
 * review session advances through this list with local state rather than
 * re-querying, so a rating's rescheduling effect can't reshuffle the queue
 * mid-session. See queryKeys.ts for why `dueCards` is a sibling key to
 * `cards`, not nested under it -- that's what makes this safe. */
export function useDueCards(deckId: string) {
  return useQuery({
    queryKey: queryKeys.dueCards(deckId),
    queryFn: () => cardsApi.due(deckId),
    staleTime: Infinity,
  });
}
