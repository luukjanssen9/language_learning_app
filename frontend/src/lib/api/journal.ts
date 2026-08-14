import { api } from "./client";
import type { JournalEntry, JournalEntrySubmitPayload } from "./types";

export const journalApi = {
  list: (userId: string, courseId: string) =>
    api.get<JournalEntry[]>(
      `/journal-entries?${new URLSearchParams({ user_id: userId, course_id: courseId })}`,
    ),
  create: (payload: JournalEntrySubmitPayload) =>
    api.post<JournalEntry>("/journal-entries", payload),
};
