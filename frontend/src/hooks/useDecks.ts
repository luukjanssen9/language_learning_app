import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { decksApi } from "@/lib/api/decks";
import type { DeckCreatePayload, DeckUpdatePayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/queryKeys";

export function useDecks() {
  return useQuery({ queryKey: queryKeys.decks, queryFn: () => decksApi.list() });
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
    mutationFn: ({ id, payload }: { id: string; payload: DeckUpdatePayload }) =>
      decksApi.update(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.decks }),
  });
}

export function useDeleteDeck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => decksApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.decks }),
  });
}
