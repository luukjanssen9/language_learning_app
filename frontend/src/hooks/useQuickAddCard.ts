import { useMutation, useQueryClient } from "@tanstack/react-query";
import { cardsApi } from "@/lib/api/cards";
import type { CardQuickAddPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/queryKeys";

export function useQuickAddCard(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CardQuickAddPayload) => cardsApi.quickAdd(userId, payload),
    // Deliberately NOT invalidating dueCards -- a due-queue is frozen for
    // the length of a review session (see queryKeys.ts), and a card
    // added mid-session shouldn't reshuffle it, same reasoning as why
    // rating a card doesn't invalidate dueCards either.
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.cards(variables.deck_id) });
      const userId = data.vocabulary_item.user_id;
      if (userId) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.vocabulary(data.vocabulary_item.course_id, userId),
        });
      }
    },
  });
}
