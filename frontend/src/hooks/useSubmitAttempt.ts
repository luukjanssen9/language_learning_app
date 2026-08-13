import { useMutation, useQueryClient } from "@tanstack/react-query";
import { lessonExercisesApi } from "@/lib/api/lessonExercises";
import { queryKeys } from "@/lib/queryKeys";
import type { UserExerciseAttemptSubmitPayload } from "@/lib/api/types";

export function useSubmitAttempt() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      exerciseId,
      payload,
    }: {
      exerciseId: string;
      payload: UserExerciseAttemptSubmitPayload;
    }) => lessonExercisesApi.submitAttempt(exerciseId, payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.progress(data.progress.user_id) });
    },
  });
}
