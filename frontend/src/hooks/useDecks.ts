import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { decksApi } from "@/lib/api/decks";
import type { DeckCreatePayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/queryKeys";

export function useDecks() {
  return useQuery({ queryKey: queryKeys.decks, queryFn: decksApi.list });
}

export function useCreateDeck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DeckCreatePayload) => decksApi.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.decks }),
  });
}
