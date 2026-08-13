import { api } from "./client";
import type { LessonExercise, LessonExerciseAttemptResponse, UserExerciseAttemptSubmitPayload } from "./types";

export const lessonExercisesApi = {
  list: (skillId: string) =>
    api.get<LessonExercise[]>(`/lesson-exercises?${new URLSearchParams({ skill_id: skillId })}`),
  submitAttempt: (exerciseId: string, payload: UserExerciseAttemptSubmitPayload) =>
    api.post<LessonExerciseAttemptResponse>(
      `/lesson-exercises/${exerciseId}/attempt`,
      payload,
    ),
};
