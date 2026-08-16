import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { readingPassagesApi } from "@/lib/api/readingPassages";
import type { ReadingPassageAttemptSubmitPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/queryKeys";

export function useReadingPassages(courseId: string, userId: string) {
  return useQuery({
    queryKey: queryKeys.readingPassages(courseId, userId),
    queryFn: () => readingPassagesApi.list(courseId, userId),
  });
}

export function useGenerateReadingPassage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ courseId, userId }: { courseId: string; userId: string }) =>
      readingPassagesApi.generate({ course_id: courseId, user_id: userId }),
    onSuccess: (data) =>
      queryClient.invalidateQueries({
        queryKey: queryKeys.readingPassages(data.course_id, data.user_id),
      }),
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
