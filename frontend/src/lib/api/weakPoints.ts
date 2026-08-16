import { api } from "./client";
import type { WeakPointsResponse } from "./types";

export const weakPointsApi = {
  get: (courseId: string) =>
    api.get<WeakPointsResponse>(`/weak-points?${new URLSearchParams({ course_id: courseId })}`),
};
