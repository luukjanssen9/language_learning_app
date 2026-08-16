import { api } from "./client";
import type {
  ReadingPassage,
  ReadingPassageAttempt,
  ReadingPassageAttemptSubmitPayload,
  ReadingPassageGeneratePayload,
} from "./types";

export const readingPassagesApi = {
  list: (courseId: string, userId: string) =>
    api.get<ReadingPassage[]>(
      `/reading-passages?${new URLSearchParams({ course_id: courseId, user_id: userId })}`,
    ),
  generate: (payload: ReadingPassageGeneratePayload) =>
    api.post<ReadingPassage>("/reading-passages", payload),
  submitAttempt: (passageId: string, payload: ReadingPassageAttemptSubmitPayload) =>
    api.post<ReadingPassageAttempt>(`/reading-passages/${passageId}/attempt`, payload),
};
