import { useQuery } from "@tanstack/react-query";
import { weakPointsApi } from "@/lib/api/weakPoints";
import { queryKeys } from "@/lib/queryKeys";

export function useWeakPoints(userId: string, courseId: string) {
  return useQuery({
    queryKey: queryKeys.weakPoints(userId, courseId),
    queryFn: () => weakPointsApi.get(userId, courseId),
  });
}
