import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { journalApi } from "@/lib/api/journal";
import type { JournalEntrySubmitPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/queryKeys";

export function useJournalEntries(userId: string, courseId: string) {
  return useQuery({
    queryKey: queryKeys.journalEntries(userId, courseId),
    queryFn: () => journalApi.list(userId, courseId),
    enabled: Boolean(userId && courseId),
  });
}

export function useSubmitJournalEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: JournalEntrySubmitPayload) => journalApi.create(payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.journalEntries(data.user_id, data.course_id),
      });
    },
  });
}
