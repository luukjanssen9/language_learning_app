import { useQuery } from "@tanstack/react-query";
import { languagesApi } from "@/lib/api/languages";
import { queryKeys } from "@/lib/queryKeys";

export function useLanguages() {
  return useQuery({ queryKey: queryKeys.languages, queryFn: languagesApi.list });
}
