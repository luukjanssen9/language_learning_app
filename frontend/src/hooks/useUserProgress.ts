import { useQuery } from "@tanstack/react-query";
import { userProgressApi } from "@/lib/api/userProgress";
import { queryKeys } from "@/lib/queryKeys";

export function useUserProgress(userId: string) {
  return useQuery({
    queryKey: queryKeys.progress(userId),
    queryFn: () => userProgressApi.list(userId),
  });
}
