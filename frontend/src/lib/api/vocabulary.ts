import { api } from "./client";
import type { VocabularyExample, VocabularyItem } from "./types";

export const vocabularyApi = {
  list: (courseId: string) =>
    api.get<VocabularyItem[]>(`/vocabulary-items?${new URLSearchParams({ course_id: courseId })}`),
  examples: (id: string) => api.get<VocabularyExample[]>(`/vocabulary-items/${id}/examples`),
};
