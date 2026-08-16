import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { cardsApi } from "@/lib/api/cards";
import type { CardCreatePayload, CardUpdatePayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/queryKeys";

export function useCards(deckId: string, userId: string) {
  return useQuery({
    queryKey: queryKeys.cards(deckId),
    queryFn: () => cardsApi.list(deckId, userId),
  });
}

export function useCreateCard(deckId: string, userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CardCreatePayload) => cardsApi.create(userId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.cards(deckId) }),
  });
}

export function useUpdateCard(deckId: string, userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CardUpdatePayload }) =>
      cardsApi.update(id, userId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.cards(deckId) }),
  });
}

export function useDeleteCard(deckId: string, userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => cardsApi.remove(id, userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.cards(deckId) }),
  });
}
