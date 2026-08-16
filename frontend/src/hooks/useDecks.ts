import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { decksApi } from "@/lib/api/decks";
import type { DeckCreatePayload, DeckUpdatePayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/queryKeys";

export function useDecks(userId: string) {
  return useQuery({ queryKey: queryKeys.decks, queryFn: () => decksApi.list(userId) });
}

export function useCreateDeck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DeckCreatePayload) => decksApi.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.decks }),
  });
}

export function useUpdateDeck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      userId,
      payload,
    }: {
      id: string;
      userId: string;
      payload: DeckUpdatePayload;
    }) => decksApi.update(id, userId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.decks }),
  });
}

export function useDeleteDeck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, userId }: { id: string; userId: string }) => decksApi.remove(id, userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.decks }),
  });
}
