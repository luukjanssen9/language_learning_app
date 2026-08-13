import { useQuery } from "@tanstack/react-query";
import { lessonExercisesApi } from "@/lib/api/lessonExercises";
import { queryKeys } from "@/lib/queryKeys";

/** Fetched once and frozen for the session (`staleTime: Infinity`) -- a
 * lesson session advances through this list with local state rather than
 * re-querying, same reasoning as `useDueCards`. See queryKeys.ts for why
 * `exercises` lives under its own root, not nested under `progress`. */
export function useLessonExercises(skillId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: queryKeys.exercises(skillId),
    queryFn: () => lessonExercisesApi.list(skillId),
    staleTime: Infinity,
    enabled: options?.enabled ?? true,
  });
}
