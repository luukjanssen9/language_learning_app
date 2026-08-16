import { api } from "./client";
import type {
  CardQuickAddResponse,
  KnownVocabularyBulkCreatePayload,
  KnownVocabularyBulkCreateResponse,
  KnownVocabularyFullSetResponse,
  KnownVocabularyItem,
  KnownVocabularyItemCreatePayload,
  KnownVocabularyPromotePayload,
  VocabularyItem,
} from "./types";

export const knownVocabularyApi = {
  list: (courseId: string) =>
    api.get<KnownVocabularyItem[]>(
      `/known-vocabulary?${new URLSearchParams({ course_id: courseId })}`,
    ),
  fullSet: (courseId: string) =>
    api.get<KnownVocabularyFullSetResponse>(
      `/known-vocabulary/full-set?${new URLSearchParams({ course_id: courseId })}`,
    ),
  mastered: (courseId: string) =>
    api.get<VocabularyItem[]>(
      `/known-vocabulary/mastered?${new URLSearchParams({ course_id: courseId })}`,
    ),
  create: (payload: KnownVocabularyItemCreatePayload) =>
    api.post<KnownVocabularyItem>("/known-vocabulary", payload),
  bulkCreate: (payload: KnownVocabularyBulkCreatePayload) =>
    api.post<KnownVocabularyBulkCreateResponse>("/known-vocabulary/bulk", payload),
  remove: (id: string) => api.delete(`/known-vocabulary/${id}`),
  promote: (id: string, payload: KnownVocabularyPromotePayload) =>
    api.post<CardQuickAddResponse>(`/known-vocabulary/${id}/promote`, payload),
};
