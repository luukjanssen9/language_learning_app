import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { knownVocabularyApi } from "@/lib/api/knownVocabulary";
import type {
  KnownVocabularyBulkCreatePayload,
  KnownVocabularyItemCreatePayload,
} from "@/lib/api/types";
import { queryKeys } from "@/lib/queryKeys";

export function useKnownVocabularyItems(courseId: string) {
  return useQuery({
    queryKey: queryKeys.knownVocabulary(courseId),
    queryFn: () => knownVocabularyApi.list(courseId),
  });
}

export function useAddKnownVocabulary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: KnownVocabularyItemCreatePayload) =>
      knownVocabularyApi.create(payload),
    onSuccess: (data) =>
      queryClient.invalidateQueries({ queryKey: queryKeys.knownVocabulary(data.course_id) }),
  });
}

export function useBulkAddKnownVocabulary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: KnownVocabularyBulkCreatePayload) =>
      knownVocabularyApi.bulkCreate(payload),
    onSuccess: (_data, variables) =>
      queryClient.invalidateQueries({ queryKey: queryKeys.knownVocabulary(variables.course_id) }),
  });
}

export function useDeleteKnownVocabulary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id }: { id: string; courseId: string }) => knownVocabularyApi.remove(id),
    onSuccess: (_data, variables) =>
      queryClient.invalidateQueries({ queryKey: queryKeys.knownVocabulary(variables.courseId) }),
  });
}

// Mirrors useQuickAddCard's invalidation set -- promotion is quick-add's
// twin, just fed by a known-vocabulary row instead of a typed-in form,
// plus the known-vocabulary list itself so the promoted row's badge
// updates.
export function usePromoteKnownVocabulary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, deckId }: { id: string; deckId: string }) =>
      knownVocabularyApi.promote(id, { deck_id: deckId }),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.cards(variables.deckId) });
      queryClient.invalidateQueries({
        queryKey: queryKeys.vocabulary(data.vocabulary_item.course_id),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.knownVocabulary(data.vocabulary_item.course_id),
      });
    },
  });
}
