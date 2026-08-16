import { api } from "./client";
import type { JournalEntry, JournalEntrySubmitPayload } from "./types";

export const journalApi = {
  list: (courseId: string) =>
    api.get<JournalEntry[]>(`/journal-entries?${new URLSearchParams({ course_id: courseId })}`),
  create: (payload: JournalEntrySubmitPayload) =>
    api.post<JournalEntry>("/journal-entries", payload),
};
