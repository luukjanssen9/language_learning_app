import { api, apiUrl } from "./client";
import type { VocabularyExample, VocabularyItem } from "./types";

export const vocabularyApi = {
  list: (courseId: string, userId: string) =>
    api.get<VocabularyItem[]>(
      `/vocabulary-items?${new URLSearchParams({ course_id: courseId, user_id: userId })}`,
    ),
  examples: (id: string) => api.get<VocabularyExample[]>(`/vocabulary-items/${id}/examples`),
  // Not fetched via `api` -- raw audio bytes, not JSON. Consumed directly
  // as an <audio> src by PlayAudioButton.
  audioUrl: (id: string) => apiUrl(`/vocabulary-items/${id}/audio`),
};
