import { useQuery } from "@tanstack/react-query";
import { coursesApi } from "@/lib/api/courses";
import { queryKeys } from "@/lib/queryKeys";

export function useCourses() {
  return useQuery({ queryKey: queryKeys.courses, queryFn: coursesApi.list });
}
