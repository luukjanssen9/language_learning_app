import { useQuery } from "@tanstack/react-query";
import { weakPointsApi } from "@/lib/api/weakPoints";
import { queryKeys } from "@/lib/queryKeys";

export function useWeakPoints(courseId: string) {
  return useQuery({
    queryKey: queryKeys.weakPoints(courseId),
    queryFn: () => weakPointsApi.get(courseId),
  });
}
