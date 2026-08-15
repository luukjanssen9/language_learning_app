import { api } from "./client";
import type { WeakPointsResponse } from "./types";

export const weakPointsApi = {
  get: (userId: string, courseId: string) =>
    api.get<WeakPointsResponse>(
      `/weak-points?${new URLSearchParams({ user_id: userId, course_id: courseId })}`,
    ),
};
