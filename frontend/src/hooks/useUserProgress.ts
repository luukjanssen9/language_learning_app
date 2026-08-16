import { useQuery } from "@tanstack/react-query";
import { userProgressApi } from "@/lib/api/userProgress";
import { queryKeys } from "@/lib/queryKeys";

export function useUserProgress() {
  return useQuery({
    queryKey: queryKeys.progress,
    queryFn: () => userProgressApi.list(),
  });
}
