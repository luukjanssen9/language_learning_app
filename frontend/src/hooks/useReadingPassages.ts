import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { readingPassagesApi } from "@/lib/api/readingPassages";
import type { ReadingPassageAttemptSubmitPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/queryKeys";

export function useReadingPassages(courseId: string) {
  return useQuery({
    queryKey: queryKeys.readingPassages(courseId),
    queryFn: () => readingPassagesApi.list(courseId),
  });
}

export function useGenerateReadingPassage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (courseId: string) => readingPassagesApi.generate({ course_id: courseId }),
    onSuccess: (data) =>
      queryClient.invalidateQueries({ queryKey: queryKeys.readingPassages(data.course_id) }),
  });
}

// No cache invalidation needed -- feedback is consumed directly from the
// mutation response, same as lesson-exercise attempts.
export function useSubmitReadingPassageAttempt() {
  return useMutation({
    mutationFn: ({
      passageId,
      payload,
    }: {
      passageId: string;
      payload: ReadingPassageAttemptSubmitPayload;
    }) => readingPassagesApi.submitAttempt(passageId, payload),
  });
}
