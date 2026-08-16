import { useQuery } from "@tanstack/react-query";
import { vocabularyApi } from "@/lib/api/vocabulary";
import { queryKeys } from "@/lib/queryKeys";

export function useVocabularyItems(courseId: string) {
  return useQuery({
    queryKey: queryKeys.vocabulary(courseId),
    queryFn: () => vocabularyApi.list(courseId),
  });
}

// `enabled` defaults to false-until-requested by the caller -- generating
// examples is a real (LLM-backed, first-request) network call, so it
// shouldn't fire for every row just from rendering the vocabulary list.
export function useVocabularyExamples(vocabularyItemId: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.vocabularyExamples(vocabularyItemId),
    queryFn: () => vocabularyApi.examples(vocabularyItemId),
    enabled,
    staleTime: Infinity,
  });
}
