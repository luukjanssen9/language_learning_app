import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { cardsApi } from "@/lib/api/cards";
import type { CardCreatePayload, CardUpdatePayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/queryKeys";

export function useCards(deckId: string) {
  return useQuery({
    queryKey: queryKeys.cards(deckId),
    queryFn: () => cardsApi.list(deckId),
  });
}

export function useCreateCard(deckId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CardCreatePayload) => cardsApi.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.cards(deckId) }),
  });
}

export function useUpdateCard(deckId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CardUpdatePayload }) =>
      cardsApi.update(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.cards(deckId) }),
  });
}

export function useDeleteCard(deckId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => cardsApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.cards(deckId) }),
  });
}
