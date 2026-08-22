import { useMutation, useQueryClient } from "@tanstack/react-query";
import { cardsApi } from "@/lib/api/cards";
import type { CardGeneratePayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/queryKeys";

export function useGenerateCard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CardGeneratePayload) => cardsApi.generate(payload),
    // Same invalidation as useQuickAddCard, and same reasoning for
    // leaving dueCards alone -- a card generated mid-review-session
    // shouldn't reshuffle the frozen due-queue.
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.cards(variables.deck_id) });
      queryClient.invalidateQueries({
        queryKey: queryKeys.vocabulary(data.vocabulary_item.course_id),
      });
    },
  });
}
