import { useQuery } from "@tanstack/react-query";
import { skillsApi } from "@/lib/api/skills";
import { queryKeys } from "@/lib/queryKeys";

export function useSkills(courseId: string) {
  return useQuery({
    queryKey: queryKeys.skills(courseId),
    queryFn: () => skillsApi.list(courseId),
  });
}
