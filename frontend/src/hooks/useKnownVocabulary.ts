import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { knownVocabularyApi } from "@/lib/api/knownVocabulary";
import type {
  KnownVocabularyBulkCreatePayload,
  KnownVocabularyItemCreatePayload,
} from "@/lib/api/types";
import { queryKeys } from "@/lib/queryKeys";

export function useKnownVocabularyItems(courseId: string, userId: string) {
  return useQuery({
    queryKey: queryKeys.knownVocabulary(courseId, userId),
    queryFn: () => knownVocabularyApi.list(courseId, userId),
  });
}

// The flat, complete known-word set (mastered Cards + all
// KnownVocabularyItem rows, no sampling) -- for coverage-gap analysis,
// which needs exact membership testing rather than useKnownVocabularyItems'
// row objects (which only cover the estimated half, not mastered Cards).
export function useKnownWordSet(courseId: string, userId: string) {
  return useQuery({
    queryKey: [...queryKeys.knownVocabulary(courseId, userId), "full-set"],
    queryFn: () => knownVocabularyApi.fullSet(courseId, userId),
  });
}

// The "known but never touched the known-vocabulary system" half of what
// the known-vocabulary page shows as known -- words mastered purely
// through normal deck review, complementing useKnownVocabularyItems above.
export function useMasteredVocabulary(courseId: string, userId: string) {
  return useQuery({
    queryKey: [...queryKeys.knownVocabulary(courseId, userId), "mastered"],
    queryFn: () => knownVocabularyApi.mastered(courseId, userId),
  });
}

export function useAddKnownVocabulary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: KnownVocabularyItemCreatePayload) =>
      knownVocabularyApi.create(payload),
    onSuccess: (data) =>
      queryClient.invalidateQueries({
        queryKey: queryKeys.knownVocabulary(data.course_id, data.user_id),
      }),
  });
}

export function useBulkAddKnownVocabulary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: KnownVocabularyBulkCreatePayload) =>
      knownVocabularyApi.bulkCreate(payload),
    onSuccess: (_data, variables) =>
      queryClient.invalidateQueries({
        queryKey: queryKeys.knownVocabulary(variables.course_id, variables.user_id),
      }),
  });
}

export function useDeleteKnownVocabulary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id }: { id: string; courseId: string; userId: string }) =>
      knownVocabularyApi.remove(id),
    onSuccess: (_data, variables) =>
      queryClient.invalidateQueries({
        queryKey: queryKeys.knownVocabulary(variables.courseId, variables.userId),
      }),
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
      const userId = data.vocabulary_item.user_id;
      queryClient.invalidateQueries({ queryKey: queryKeys.cards(variables.deckId) });
      if (userId) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.vocabulary(data.vocabulary_item.course_id, userId),
        });
        queryClient.invalidateQueries({
          queryKey: queryKeys.knownVocabulary(data.vocabulary_item.course_id, userId),
        });
      }
    },
  });
}
